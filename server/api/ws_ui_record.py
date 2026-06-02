"""
UI 录制 WebSocket 端点
处理录制过程中的实时截图推送和用户事件转发
"""
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ui_recorder import recording_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/ui-record/{session_id}")
async def websocket_ui_record(websocket: WebSocket, session_id: str):
    """UI 录制 WebSocket 端点"""
    await websocket.accept()

    recorder = recording_manager.get_session(session_id)
    if not recorder:
        await websocket.send_json({"type": "error", "message": "录制会话不存在"})
        await websocket.close()
        return

    # 获取当前事件循环，用于从录制线程发送消息
    main_loop = asyncio.get_event_loop()

    # 截图回调（同步函数，在录制线程中调用）
    def send_screenshot(screenshot_base64: str):
        try:
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "screenshot", "data": screenshot_base64}),
                main_loop
            )
        except Exception:
            pass

    # 步骤回调（同步函数，在录制线程中调用）
    def send_step(step: dict):
        # 判断是否是特殊消息类型（有 _msg_type 标记）
        msg_type = step.get("_msg_type")
        print(f"[WS_SEND_STEP] _msg_type={msg_type}, action={step.get('action')}, id={step.get('id')}")

        if msg_type == "element_info":
            # 元素信息响应
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({
                        "type": "element_info",
                        "element": step.get("element"),
                    }),
                    main_loop
                )
            except Exception:
                pass
        elif msg_type == "input_target":
            # 输入框信息，让前端弹出输入弹窗
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({
                        "type": "input_target",
                        "target": step.get("target"),
                    }),
                    main_loop
                )
            except Exception:
                pass
        else:
            # 普通步骤录制
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "step_recorded", "step": step}),
                    main_loop
                )
            except Exception:
                pass

    # 设置回调
    recorder._screenshot_callback = send_screenshot
    recorder._step_callback = send_step

    # 心跳任务
    async def send_heartbeat():
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(send_heartbeat())

    try:
        # 发送当前状态
        await websocket.send_json({
            "type": "status",
            "status": recorder.status,
            "url": recorder.url,
        })

        # 发送已有的步骤（WebSocket 连接前可能已经有步骤被记录）
        for step in recorder.steps:
            await websocket.send_json({"type": "step_recorded", "step": step})
            print(f"[WS_RECORD] 发送已有步骤: {step.get('action')}")

        # 监听前端消息（用户事件转发）
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                # 同步方法，内部会转发到录制线程
                recorder.inject_event(event)
            except json.JSONDecodeError:
                logger.warning(f"无效的JSON消息: {data}")
            except Exception as e:
                logger.error(f"处理事件异常: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
    finally:
        heartbeat_task.cancel()
        # 清除回调
        recorder._screenshot_callback = None
        recorder._step_callback = None
        try:
            await websocket.close()
        except Exception:
            pass
