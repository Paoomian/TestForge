"""UI 任务配置 Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UITestSuiteCreate(BaseModel):
    """创建 UI 任务配置"""
    project_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    case_ids: list[int] = []
    environment_id: Optional[int] = None
    failure_strategy: str = "continue"
    browser: str = "chrome"
    viewport_width: int = 1280
    viewport_height: int = 720
    tags: list[str] = []


class UITestSuiteUpdate(BaseModel):
    """更新 UI 任务配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    case_ids: Optional[list[int]] = None
    environment_id: Optional[int] = None
    failure_strategy: Optional[str] = None
    browser: Optional[str] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    tags: Optional[list[str]] = None


class UITestSuiteOut(BaseModel):
    """UI 任务配置输出"""
    id: int
    project_id: int
    project_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    case_ids: list[int] = []
    case_count: int = 0
    environment_id: Optional[int] = None
    environment_name: Optional[str] = None
    failure_strategy: str
    browser: str
    viewport_width: int
    viewport_height: int
    tags: list[str] = []
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
