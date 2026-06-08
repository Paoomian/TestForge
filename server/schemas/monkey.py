"""Monkey 测试相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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


class MonkeyPresetCreate(BaseModel):
    """创建 Monkey 预设"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    pct_touch: int = Field(15, ge=0, le=100)
    pct_motion: int = Field(10, ge=0, le=100)
    pct_trackball: int = Field(15, ge=0, le=100)
    pct_nav: int = Field(20, ge=0, le=100)
    pct_majornav: int = Field(15, ge=0, le=100)
    pct_syskeys: int = Field(5, ge=0, le=100)
    pct_appswitch: int = Field(2, ge=0, le=100)
    pct_anyevent: int = Field(18, ge=0, le=100)
    event_count: int = Field(1000, ge=1)
    interval: int = Field(300, ge=0)


class MonkeyPresetUpdate(BaseModel):
    """更新 Monkey 预设"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    pct_touch: Optional[int] = Field(None, ge=0, le=100)
    pct_motion: Optional[int] = Field(None, ge=0, le=100)
    pct_trackball: Optional[int] = Field(None, ge=0, le=100)
    pct_nav: Optional[int] = Field(None, ge=0, le=100)
    pct_majornav: Optional[int] = Field(None, ge=0, le=100)
    pct_syskeys: Optional[int] = Field(None, ge=0, le=100)
    pct_appswitch: Optional[int] = Field(None, ge=0, le=100)
    pct_anyevent: Optional[int] = Field(None, ge=0, le=100)
    event_count: Optional[int] = Field(None, ge=1)
    interval: Optional[int] = Field(None, ge=0)


class MonkeyPresetOut(BaseModel):
    """Monkey 预设输出"""
    id: int
    name: str
    pct_touch: int
    pct_motion: int
    pct_trackball: int
    pct_nav: int
    pct_majornav: int
    pct_syskeys: int
    pct_appswitch: int
    pct_anyevent: int
    event_count: int
    interval: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
