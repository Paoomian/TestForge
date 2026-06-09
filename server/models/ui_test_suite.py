"""UI 自动化任务配置模型"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UITestSuite(Base):
    """UI 自动化任务配置"""
    __tablename__ = "ui_test_suites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 用例配置
    case_ids = Column(JSON, default=list)  # UI 用例 ID 列表

    # 默认执行配置
    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=True)
    failure_strategy = Column(String(20), default="continue")  # continue / stop

    # 浏览器配置
    browser = Column(String(20), default="chrome")  # chrome / firefox / edge
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=720)

    # 标签
    tags = Column(JSON, default=list)

    # 审计字段
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    project = relationship("Project")
    environment = relationship("Environment")
    creator = relationship("User")
