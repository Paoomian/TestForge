from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class TestSuite(Base):
    """测试任务配置（用例组合）"""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 用例配置
    case_ids = Column(JSON, default=list)  # 用例ID列表

    # 默认执行配置
    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=True)
    concurrency = Column(Integer, default=1)  # 1/3/5/10
    failure_strategy = Column(String(20), default="continue")  # continue / stop
    variables = Column(JSON, default=dict)  # 额外变量

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
