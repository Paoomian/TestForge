"""Monkey 测试 WebSocket - 实时日志推送"""
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.adb_service import adb_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/monkey/{task_id}")
async def ws_monkey_log(websocket: WebSocket, task_id: str):
    """WebSocket 实时推送 Monkey 日志"""
    await websocket.accept()

    task = adb_service.get_task(task_id)
    if not task:
        await websocket.send_json({"type": "error", "message": "任务不存在"})
        await websocket.close()
        return

    # 注册日志回调，将新日志行推送给客户端
    sent_count = 0

    async def send_log(line: str):
        try:
            await websocket.send_json({"type": "log", "line": line})
        except Exception:
            pass

    def log_callback(tid: str, line: str):
        nonlocal sent_count
        sent_count += 1
        # 通过事件循环异步发送
        try:
            asyncio.run_coroutine_threadsafe(send_log(line), loop)
        except Exception:
            pass

    loop = asyncio.get_event_loop()
    task._log_callback = log_callback

    try:
        # 先发送已有的日志
        for line in task.output_lines:
            await websocket.send_json({"type": "log", "line": line})

        # 持续监听直到任务结束或客户端断开
        while task.status == "running":
            try:
                # 非阻塞接收客户端消息（如停止命令）
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                msg = json.loads(data)
                if msg.get("action") == "stop":
                    adb_service.stop_monkey(task_id)
                    await websocket.send_json({"type": "status", "status": "stopped"})
                    break
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass

        # 任务结束，发送最终状态
        if task.status != "running":
            await websocket.send_json({"type": "status", "status": task.status})

    except WebSocketDisconnect:
        logger.info(f"[MONKEY WS] 客户端断开: {task_id}")
    except Exception as e:
        logger.error(f"[MONKEY WS] 异常: {e}")
    finally:
        task._log_callback = None
