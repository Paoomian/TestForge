"""Monkey 测试相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class MonkeyConfig(BaseModel):
    """Monkey 测试配置"""
    device_serial: str = Field(..., description="设备序列号")
    event_count: int = Field(1000, ge=1, description="事件总数")
    interval: int = Field(300, ge=0, description="事件间隔(ms)")
    seed: Optional[int] = Field(None, description="随机种子")
    package: Optional[str] = Field(None, description="目标包名")
    # 各事件类型百分比
    pct_touch: int = Field(15, ge=0, le=100, description="触摸事件(%)")
    pct_motion: int = Field(10, ge=0, le=100, description="滑动事件(%)")
    pct_trackball: int = Field(15, ge=0, le=100, description="轨迹球事件(%)")
    pct_nav: int = Field(20, ge=0, le=100, description="基本导航事件(%)")
    pct_majornav: int = Field(15, ge=0, le=100, description="主要导航事件(%)")
    pct_syskeys: int = Field(5, ge=0, le=100, description="系统按键事件(%)")
    pct_appswitch: int = Field(2, ge=0, le=100, description="Activity切换(%)")
    pct_anyevent: int = Field(18, ge=0, le=100, description="其他事件(%)")


class MonkeyTaskResponse(BaseModel):
    """Monkey 任务响应"""
    task_id: str
    device_serial: str
    status: str


class DeviceInfoSchema(BaseModel):
    """设备信息"""
    serial: str
    status: str
    model: str = ""
