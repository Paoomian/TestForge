import asyncio
from celery_app import celery_app
from database import SessionLocal
from services.batch_runner import BatchRunner


@celery_app.task(bind=True, name="tasks.batch_run")
def batch_run_task(self, test_run_id: int):
    """批量执行 Celery 任务"""
    db = SessionLocal()
    try:
        runner = BatchRunner(db, test_run_id, self.request.id)
        # 在 Celery Worker 中运行异步代码
        asyncio.run(runner.execute())
    finally:
        db.close()
