from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ============================================================
# 单用例执行 Schemas（原有）
# ============================================================

class RunRequest(BaseModel):
    """执行请求"""
    environment_id: Optional[int] = None
    variables: dict[str, str] = {}


class AssertionResult(BaseModel):
    """单条断言结果"""
    assertion_type: str
    field: Optional[str] = None
    operator: str
    expected: str
    actual: Optional[str] = None
    passed: bool
    error: Optional[str] = None


class RunResult(BaseModel):
    """执行结果"""
    status: str  # pass / fail / error
    request_snapshot: Optional[dict] = None
    response_info: Optional[dict] = None
    assertions: list[AssertionResult] = []
    extracted_variables: dict[str, str] = {}
    script_output: dict = {}
    error_message: Optional[str] = None
    duration_ms: int = 0


# ============================================================
# 批量执行 Schemas
# ============================================================

class BatchRunCreate(BaseModel):
    """创建批量执行任务"""
    case_ids: list[int]
    environment_id: Optional[int] = None
    concurrency: int = 1  # 1/3/5/10
    failure_strategy: str = "continue"  # continue / stop
    variables: dict[str, str] = {}


class BatchRunDetailSummary(BaseModel):
    """用例执行结果摘要（列表展示）"""
    id: int
    case_id: int
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    execution_order: int
    status: str
    duration_ms: int = 0  # 总耗时（含框架开销）
    api_duration_ms: Optional[int] = None  # 接口响应耗时
    status_code: Optional[int] = None  # 响应状态码
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class BatchRunDetailFull(BaseModel):
    """用例执行完整详情"""
    id: int
    test_run_id: int
    case_id: int
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    execution_order: int
    status: str
    request_snapshot: Optional[dict] = None
    response_info: Optional[dict] = None
    assertions: list = []
    extracted_vars: dict = {}
    script_output: dict = {}
    error_message: Optional[str] = None
    duration_ms: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchRunList(BaseModel):
    """任务列表项"""
    id: int
    name: str
    status: str
    concurrency: int
    failure_strategy: str
    total_count: int
    pass_count: int
    fail_count: int
    error_count: int
    progress: float  # 百分比 0-100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BatchRunInfo(BaseModel):
    """任务详情（含用例结果摘要）"""
    id: int
    project_id: int
    name: str
    status: str
    case_ids: list[int]
    environment_id: Optional[int] = None
    concurrency: int
    failure_strategy: str
    variables: dict = {}
    total_count: int
    pass_count: int
    fail_count: int
    error_count: int
    progress: float
    celery_task_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    creator_id: Optional[int] = None
    created_at: datetime
    details: list[BatchRunDetailSummary] = []

    class Config:
        from_attributes = True


# ============================================================
# WebSocket 消息 Schemas
# ============================================================

class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str  # task_start / case_start / case_finish / task_finish / task_cancelled / ping
    task_id: Optional[int] = None
    detail_id: Optional[int] = None
    case_name: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None
    duration_ms: Optional[int] = None
    total: Optional[int] = None
    pass_count: Optional[int] = None
    fail_count: Optional[int] = None
    error_count: Optional[int] = None
