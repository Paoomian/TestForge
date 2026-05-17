from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


class TestRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


class TestRunDetailStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    test_type = Column(String(50), nullable=False, default="api_batch")

    # 执行配置
    case_ids = Column(JSON, default=list)
    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=True)
    concurrency = Column(Integer, default=1)  # 1/3/5/10
    failure_strategy = Column(String(20), default="continue")  # continue / stop
    variables = Column(JSON, default=dict)  # 任务级变量

    # 状态
    status = Column(String(20), default=TestRunStatus.PENDING.value)
    celery_task_id = Column(String(200), nullable=True)  # Celery任务ID，用于取消
    cancelled = Column(Boolean, default=False)  # 取消标志

    # 统计
    total_count = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # 结果
    result = Column(JSON, default=dict)
    logs = Column(JSON, default=list)

    # 时间
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # 毫秒

    # 审计
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    details = relationship("TestRunDetail", back_populates="test_run", order_by="TestRunDetail.execution_order")


class TestRunDetail(Base):
    __tablename__ = "test_run_details"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="SET NULL"), nullable=True)
    case_name = Column(String(200), nullable=True)   # 执行时快照，删用例后保留
    case_number = Column(String(50), nullable=True)   # 执行时快照，删用例后保留
    execution_order = Column(Integer, default=0)

    # 执行状态
    status = Column(String(20), default=TestRunDetailStatus.PENDING.value)

    # 请求/响应快照
    request_snapshot = Column(JSON, nullable=True)
    response_info = Column(JSON, nullable=True)

    # 断言结果
    assertions = Column(JSON, default=list)

    # 提取的变量
    extracted_vars = Column(JSON, default=dict)

    # 脚本输出
    script_output = Column(JSON, default=dict)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 时间
    duration_ms = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    test_run = relationship("TestRun", back_populates="details")
    case = relationship("APITestCase")
