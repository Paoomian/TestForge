from pydantic import BaseModel, Field


class ExcelHeaderItem(BaseModel):
    """Excel 导入的 Header 项"""
    enabled: bool = True
    key: str
    value: str = ""
    description: str = ""


class ExcelQueryParamItem(BaseModel):
    """Excel 导入的查询参数项"""
    enabled: bool = True
    key: str
    value: str = ""
    description: str = ""


class ExcelBodyFormItem(BaseModel):
    """Excel 导入的表单 Body 项"""
    enabled: bool = True
    key: str
    value: str = ""
    param_type: str = "text"
    description: str = ""


class ExcelAssertionItem(BaseModel):
    """Excel 导入的断言项"""
    assertion_type: str = Field(..., description="status_code/jsonpath/header/body_contains")
    operator: str = Field(..., description="equals/not_equals/contains/greater_than/less_than")
    field: str = ""
    expected: str = ""
    description: str = ""


class ExcelDataRuleItem(BaseModel):
    """Excel 导入的数据规则项（含提取规则）"""
    name: str = Field(..., description="变量名")
    rule_type: str = Field(default="extract", description="extract/static/generate/transform/conditional")
    source: str | None = None  # extract 类型：jsonpath/regex/header
    expression: str | None = None  # extract 类型：提取表达式
    default_value: str = ""
    description: str = ""


class ExcelCaseItem(BaseModel):
    """Excel 导入的单条用例"""
    # 主表字段
    name: str = Field(..., min_length=1, max_length=200)
    method: str = Field(..., description="GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS")
    url: str = Field(..., min_length=1)
    module: str | None = None
    priority: str = Field(default="P2", description="P0/P1/P2/P3")
    description: str | None = None
    preconditions: str | None = None
    body_type: str = Field(default="none", description="none/form-data/raw-json/raw-xml/raw-text")
    body_raw_content: str | None = None
    remark: str | None = None

    # 子表字段
    headers: list[ExcelHeaderItem] = []
    query_params: list[ExcelQueryParamItem] = []
    body_form: list[ExcelBodyFormItem] = []
    assertions: list[ExcelAssertionItem] = []
    data_rules: list[ExcelDataRuleItem] = []


class ExcelImportRequest(BaseModel):
    """Excel 导入请求"""
    cases: list[ExcelCaseItem]
    project_id: int


class ImportError(BaseModel):
    """导入错误详情"""
    row: int
    name: str
    error: str


class ExcelImportResult(BaseModel):
    """导入结果"""
    total: int
    success: int
    failed: int
    created_ids: list[int]
    errors: list[ImportError]
