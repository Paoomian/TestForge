"""
UI 用例执行 WebSocket 端点
支持实时截图推送和执行进度
"""
import asyncio
import json
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UICase, Environment
from services.ui_executor import UIExecutor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/ui-run/{case_id}")
async def websocket_ui_run(websocket: WebSocket, case_id: int, environment_id: int = None):
    """UI 用例执行 WebSocket 端点"""
    await websocket.accept()

    # 获取用例和环境变量
    db = SessionLocal()
    try:
        case = db.query(UICase).filter(UICase.id == case_id).first()
        if not case:
            await websocket.send_json({"type": "error", "message": "用例不存在"})
            await websocket.close()
            return

        if not case.steps:
            await websocket.send_json({"type": "error", "message": "用例没有步骤"})
            await websocket.close()
            return

        # 加载环境变量
        base_url = ""
        variables = {}
        if environment_id:
            env = db.query(Environment).filter(Environment.id == environment_id).first()
            if env:
                base_url = env.base_url or ""
                variables = env.variables or {}
                print(f"[WS_RUN] 加载环境: {env.name}, base_url: {base_url}")
    finally:
        db.close()

    # 获取当前事件循环
    main_loop = asyncio.get_event_loop()

    # 创建执行器
    session_id = str(uuid.uuid4())[:8]
    executor = UIExecutor(session_id)

    # 截图回调
    def send_screenshot(screenshot_base64: str):
        try:
            future = asyncio.run_coroutine_threadsafe(
                websocket.send_json({
                    "type": "screenshot",
                    "data": screenshot_base64,
                }),
                main_loop
            )
            future.result(timeout=1)
        except Exception as e:
            if "closed" not in str(e).lower():
                print(f"[WS_RUN] 截图发送失败: {e}")

    # 心跳任务
    async def send_heartbeat():
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(send_heartbeat())

    # 执行完成事件
    execution_done = asyncio.Event()

    # 包装进度回调，检测完成状态
    def send_progress_with_done(progress: dict):
        try:
            # 将进度类型改为 progress_type，避免与消息类型冲突
            progress_data = {
                "type": "progress",
                "progress_type": progress.get("type", ""),
                **{k: v for k, v in progress.items() if k != "type"},
            }
            print(f"[WS_RUN] 发送进度: {progress_data.get('progress_type')}, step={progress_data.get('current')}")
            future = asyncio.run_coroutine_threadsafe(
                websocket.send_json(progress_data),
                main_loop
            )
            future.result(timeout=1)
        except Exception as e:
            if "closed" not in str(e).lower():
                print(f"[WS_RUN] 进度发送失败: {e}")

        # 检测完成
        if progress.get("type") == "completed":
            main_loop.call_soon_threadsafe(execution_done.set)

    try:
        # 发送开始消息
        print(f"[WS_RUN] 开始执行用例: {case.name}, 共 {len(case.steps)} 步")
        await websocket.send_json({
            "type": "started",
            "case_id": case_id,
            "case_name": case.name,
            "total_steps": len(case.steps),
        })

        # 启动执行
        executor.start(
            steps=case.steps,
            base_url=base_url or case.base_url or "",
            variables=variables,
            viewport_width=1280,
            viewport_height=720,
            screenshot_callback=send_screenshot,
            progress_callback=send_progress_with_done,
        )

        # 等待执行完成或用户取消
        while not execution_done.is_set():
            try:
                # 检查是否有取消命令
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                try:
                    event = json.loads(data)
                    if event.get("type") == "command" and event.get("action") == "stop":
                        print("[WS_RUN] 用户停止执行")
                        executor.stop()
                        break
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                continue

        # 等待执行线程结束
        print("[WS_RUN] 等待执行线程结束...")
        if executor._thread:
            executor._thread.join(timeout=10)

        print(f"[WS_RUN] 执行完成: {executor.status}")
        # 发送完成消息
        await websocket.send_json({
            "type": "completed",
            "status": executor.status,
            "results": executor.results,
        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: {case_id}")
        executor.stop()
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        heartbeat_task.cancel()
        executor.stop()
        try:
            await websocket.close()
        except Exception:
            pass
