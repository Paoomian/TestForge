import json
import asyncio
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.config import settings

router = APIRouter()


@router.websocket("/ws/batch/{run_id}")
async def websocket_batch_progress(websocket: WebSocket, run_id: int):
    """WebSocket 连接，接收批量执行进度"""
    await websocket.accept()

    # Redis Pub/Sub 连接
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    channel = f"batch_run:{run_id}"

    try:
        # 订阅频道
        await pubsub.subscribe(channel)

        # 心跳任务
        async def send_heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(send_heartbeat())

        # 监听消息
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # 转发给前端
                    if isinstance(data, str):
                        await websocket.send_text(data)
                    else:
                        await websocket.send_json(data)
        except WebSocketDisconnect:
            pass
        finally:
            heartbeat_task.cancel()

    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        await pubsub.unsubscribe(channel)
        await redis.close()
        try:
            await websocket.close()
        except Exception:
            pass
