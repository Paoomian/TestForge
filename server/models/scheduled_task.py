"""定时任务模型"""
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class ScheduledTask(Base):
    """定时执行任务配置"""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    task_type = Column(String(20), nullable=False, default="api_batch")  # api_batch / ui_batch / api_scene
    suite_id = Column(Integer, nullable=False)  # 关联的测试套件 ID
    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=True)
    concurrency = Column(Integer, default=1)  # 1/3/5/10
    failure_strategy = Column(String(20), default="continue")  # continue / stop
    variables = Column(JSON, default=dict)
    cron_expression = Column(String(100), nullable=False)  # Cron 表达式
    enabled = Column(Boolean, default=True)  # 是否启用
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
