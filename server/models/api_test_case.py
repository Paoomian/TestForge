from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class APITestCase(Base):
    __tablename__ = "api_test_cases"

    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    module = Column(String(200))
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # 请求配置
    method = Column(String(10), nullable=False)
    url = Column(Text, nullable=False)
    headers = Column(JSON, default=dict)
    body = Column(Text)
    query_params = Column(JSON, default=dict)

    # 变量和脚本
    variables = Column(JSON, default=dict)
    setup_script = Column(Text)
    teardown_script = Column(Text)

    # 断言配置
    assertions = Column(JSON, default=list)

    # 元数据
    tags = Column(JSON, default=list)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="active")

    # 版本控制
    version = Column(Integer, default=1)

    # 审计字段
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="api_test_cases")
    creator = relationship("User")
    histories = relationship("APITestCaseHistory", back_populates="test_case", cascade="all, delete-orphan")
