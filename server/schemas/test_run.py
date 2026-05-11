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
    environment_name: Optional[str] = None
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
# 测试报告 Schemas
# ============================================================

class TestSummary(BaseModel):
    """测试摘要"""
    total_count: int
    pass_count: int
    fail_count: int
    error_count: int
    skipped_count: int
    pass_rate: float  # 百分比 0-100, 保留1位小数
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None


class APICallStat(BaseModel):
    """单条接口性能统计"""
    case_id: int
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    api_duration_ms: int


class PerformanceStats(BaseModel):
    """性能统计"""
    avg_response_ms: float  # 平均响应时间(ms)
    min_response_ms: int  # 最快响应时间
    max_response_ms: int  # 最慢响应时间
    p50_response_ms: int  # P50
    p90_response_ms: int  # P90
    p95_response_ms: int  # P95
    total_requests: int  # 有效请求总数（有 elapsed_ms 的）
    slowest_top5: list[APICallStat]  # 最慢 Top5
    fastest_top5: list[APICallStat]  # 最快 Top5


class FailureCategory(BaseModel):
    """失败分类"""
    category: str  # 分类名，如 "断言失败" / "请求超时" / "执行异常"
    count: int
    percentage: float  # 占全部失败+错误的百分比
    cases: list[dict]  # [{case_id, case_name, error_message}]


class FailureAnalysis(BaseModel):
    """失败分析"""
    total_fail_count: int  # fail + error 总数
    categories: list[FailureCategory]


class BatchRunReport(BaseModel):
    """完整测试报告"""
    summary: TestSummary
    performance: PerformanceStats
    failure_analysis: FailureAnalysis


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
