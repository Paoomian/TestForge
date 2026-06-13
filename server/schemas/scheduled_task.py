"""定时任务 Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScheduledTaskCreate(BaseModel):
    """创建定时任务"""
    name: str
    task_type: str = "api_batch"  # api_batch / ui_batch / api_scene
    suite_id: int
    environment_id: Optional[int] = None
    concurrency: int = 1
    failure_strategy: str = "continue"
    variables: dict[str, str] = {}
    cron_expression: str  # 如 "0 9 * * 1-5"
    enabled: bool = True


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务"""
    name: Optional[str] = None
    task_type: Optional[str] = None
    suite_id: Optional[int] = None
    environment_id: Optional[int] = None
    concurrency: Optional[int] = None
    failure_strategy: Optional[str] = None
    variables: Optional[dict[str, str]] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduledTaskOut(BaseModel):
    """定时任务输出"""
    id: int
    name: str
    task_type: str
    suite_id: int
    suite_name: Optional[str] = None  # 套件名称（关联查询）
    environment_id: Optional[int] = None
    environment_name: Optional[str] = None
    concurrency: int
    failure_strategy: str
    variables: dict
    cron_expression: str
    enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
