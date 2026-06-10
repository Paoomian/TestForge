from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UICase(Base):
    __tablename__ = "ui_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    case_number = Column(String(50))  # 用例编号
    module = Column(String(200))  # 所属模块（树形路径，如"用户管理/登录"）
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(10), default="P2")  # 优先级: P0/P1/P2/P3
    steps = Column(JSON, default=list)
    locators = Column(JSON, default=dict)
    assertions = Column(JSON, default=list)
    # 录制相关扩展字段
    base_url = Column(String(500), nullable=True)  # 录制目标URL
    browser_config = Column(JSON, nullable=True)  # 浏览器配置（视口大小、UA等）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="ui_cases")
