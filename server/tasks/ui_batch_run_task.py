"""
UI 批量执行 Celery 任务
"""
import asyncio
from celery_app import celery_app
from database import SessionLocal
from services.ui_batch_runner import UIBatchRunner


@celery_app.task(bind=True, name="tasks.ui_batch_run")
def ui_batch_run_task(self, test_run_id: int, browser: str = "chrome", viewport_width: int = 1280, viewport_height: int = 720):
    """UI 批量执行任务入口"""
    db = SessionLocal()
    try:
        runner = UIBatchRunner(
            db=db,
            test_run_id=test_run_id,
            celery_task_id=self.request.id,
            browser=browser,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )
        asyncio.run(runner.execute())
    finally:
        db.close()
