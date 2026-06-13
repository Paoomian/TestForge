import sys
import os
from celery import Celery
from core.config import settings

# 确保当前目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建 Celery 实例
celery_app = Celery(
    "testforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# 配置
celery_app.conf.update(
    # 序列化方式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果过期时间（1小时）
    result_expires=3600,

    # 任务确认方式
    task_acks_late=True,

    # Worker 预取数量（并发控制）
    worker_prefetch_multiplier=1,

    # 任务软超时（30分钟）
    task_soft_time_limit=1800,

    # 任务硬超时（35分钟）
    task_time_limit=2100,

    # Windows 兼容
    worker_pool="solo",
)

# 使用 include 直接指定任务模块，避免自动发现
celery_app.conf.include = [
    "tasks.batch_run_task",
    "tasks.scene_run_task",
    "tasks.ai_generate_tasks",
    "tasks.ui_batch_run_task",
    "tasks.scheduler_task",
]

# Celery Beat 定时调度配置
celery_app.conf.beat_schedule = {
    "scheduler-tick-every-minute": {
        "task": "tasks.scheduler_tick",
        "schedule": 60.0,  # 每 60 秒执行一次
    },
}
