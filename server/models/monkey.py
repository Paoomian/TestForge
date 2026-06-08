"""Monkey 测试预设配置模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from database import Base


class MonkeyPreset(Base):
    """Monkey 事件配置预设"""
    __tablename__ = "monkey_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 事件百分比配置
    pct_touch = Column(Integer, default=15, comment="触摸事件(%)")
    pct_motion = Column(Integer, default=10, comment="滑动事件(%)")
    pct_trackball = Column(Integer, default=15, comment="轨迹球(%)")
    pct_nav = Column(Integer, default=20, comment="基本导航(%)")
    pct_majornav = Column(Integer, default=15, comment="主要导航(%)")
    pct_syskeys = Column(Integer, default=5, comment="系统按键(%)")
    pct_appswitch = Column(Integer, default=2, comment="Activity切换(%)")
    pct_anyevent = Column(Integer, default=18, comment="其他事件(%)")

    # 基本参数
    event_count = Column(Integer, default=1000, comment="事件总数")
    interval = Column(Integer, default=300, comment="事件间隔(ms)")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
