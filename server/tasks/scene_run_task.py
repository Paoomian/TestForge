import asyncio
from celery_app import celery_app
from database import SessionLocal
from services.scene_runner import SceneRunner


@celery_app.task(bind=True, name="tasks.scene_run")
def scene_run_task(self, test_run_id: int):
    """场景编排执行 Celery 任务"""
    db = SessionLocal()
    try:
        runner = SceneRunner(db, test_run_id, self.request.id)
        asyncio.run(runner.execute())
    finally:
        db.close()
