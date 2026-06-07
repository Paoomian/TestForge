from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UIStepBase(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None


class UICaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list[dict] = []
    locators: dict = {}
    assertions: list[dict] = []
    base_url: Optional[str] = None
    browser_config: Optional[dict] = None


class UICaseCreate(UICaseBase):
    project_id: int


class UICaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list[dict]] = None
    locators: Optional[dict] = None
    assertions: Optional[list[dict]] = None
    base_url: Optional[str] = None
    browser_config: Optional[dict] = None


class UICaseInDB(UICaseBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 录制相关 Schema ==========

class RecordingStartRequest(BaseModel):
    """启动录制请求"""
    url: str  # 目标页面URL
    project_id: int  # 所属项目
    environment_id: Optional[int] = None  # 环境ID（用于URL参数化）
    base_url: Optional[str] = None  # 基础URL（用于变量替换，如 http://dev.example.com）
    viewport_width: int = 1280  # 浏览器视口宽度
    viewport_height: int = 720  # 浏览器视口高度
    user_agent: Optional[str] = None  # 自定义UA


class RecordingStopRequest(BaseModel):
    """停止录制请求"""
    name: str  # 用例名称
    description: Optional[str] = None  # 用例描述
    project_id: int  # 保存到的项目ID
    save_to_project: bool = True  # 是否保存到项目
    steps: Optional[list[dict]] = None  # 前端传入的步骤（可选，覆盖录制器中的步骤）


class RecordingSession(BaseModel):
    """录制会话信息"""
    session_id: str
    status: str  # connecting / recording / paused / stopped
    url: str
    websocket_url: str  # WebSocket连接地址
