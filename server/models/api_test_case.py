from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class APITestCase(Base):
    __tablename__ = "api_test_cases"

    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    case_number = Column(String(50))
    module = Column(String(200))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    preconditions = Column(Text)
    remark = Column(Text)

    # 请求配置
    method = Column(String(10), nullable=False)
    url = Column(Text, nullable=False)
    body_type = Column(String(20), default="none")  # none/form-data/x-www-form-urlencoded/raw-json/raw-xml/raw-text
    auth_type = Column(String(20), default="none")  # none/bearer/basic/api_key

    # 脚本
    setup_script = Column(Text)
    teardown_script = Column(Text)

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

    # 关系 - 主表
    project = relationship("Project", back_populates="api_test_cases")
    creator = relationship("User")
    histories = relationship("APITestCaseHistory", back_populates="test_case", cascade="all, delete-orphan")

    # 关系 - 子表
    headers = relationship("TestCaseHeader", cascade="all, delete-orphan", order_by="TestCaseHeader.sort_order")
    query_params = relationship("TestCaseQueryParam", cascade="all, delete-orphan", order_by="TestCaseQueryParam.sort_order")
    body_form = relationship("TestCaseBodyForm", cascade="all, delete-orphan", order_by="TestCaseBodyForm.sort_order")
    body_raw = relationship("TestCaseBodyRaw", uselist=False, cascade="all, delete-orphan")
    assertions = relationship("TestCaseAssertion", cascade="all, delete-orphan", order_by="TestCaseAssertion.sort_order")
    extracts = relationship("TestCaseExtract", cascade="all, delete-orphan", order_by="TestCaseExtract.sort_order")
    auth = relationship("TestCaseAuth", uselist=False, cascade="all, delete-orphan")
