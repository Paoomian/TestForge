from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TestSuiteCreate(BaseModel):
    """创建任务配置"""
    project_id: int
    name: str
    description: Optional[str] = None
    config_mode: str = "simple"  # simple / orchestration
    case_ids: list[int] = []
    environment_id: Optional[int] = None
    concurrency: int = 1
    failure_strategy: str = "continue"
    variables: dict[str, str] = {}
    tags: list[str] = []


class TestSuiteUpdate(BaseModel):
    """更新任务配置"""
    name: Optional[str] = None
    description: Optional[str] = None
    config_mode: Optional[str] = None
    case_ids: Optional[list[int]] = None
    environment_id: Optional[int] = None
    concurrency: Optional[int] = None
    failure_strategy: Optional[str] = None
    variables: Optional[dict[str, str]] = None
    tags: Optional[list[str]] = None


class TestSuiteInfo(BaseModel):
    """任务配置详情"""
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    config_mode: str = "simple"
    case_ids: list[int] = []
    case_count: int = 0  # 用例数量
    environment_id: Optional[int] = None
    environment_name: Optional[str] = None
    concurrency: int = 1
    failure_strategy: str = "continue"
    variables: dict[str, str] = {}
    tags: list[str] = []
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestSuiteList(BaseModel):
    """任务配置列表项"""
    id: int
    project_id: int
    project_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    config_mode: str = "simple"
    case_count: int = 0
    environment_name: Optional[str] = None
    concurrency: int = 1
    failure_strategy: str = "continue"
    tags: list[str] = []
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestSuiteRunRequest(BaseModel):
    """执行任务配置请求（可覆盖默认配置）"""
    environment_id: Optional[int] = None
    concurrency: Optional[int] = None
    failure_strategy: Optional[str] = None
    variables: Optional[dict[str, str]] = None
