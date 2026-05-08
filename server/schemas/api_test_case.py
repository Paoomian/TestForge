from typing import Optional
from datetime import datetime
from pydantic import BaseModel


# ============================================================
# 子表 Schemas
# ============================================================

class HeaderItem(BaseModel):
    enabled: bool = True
    key: str
    value: Optional[str] = ""
    description: Optional[str] = ""
    sort_order: int = 0


class QueryParamItem(BaseModel):
    enabled: bool = True
    key: str
    value: Optional[str] = ""
    description: Optional[str] = ""
    sort_order: int = 0


class BodyFormItem(BaseModel):
    enabled: bool = True
    key: str
    value: Optional[str] = ""
    param_type: str = "text"  # text / file
    description: Optional[str] = ""
    sort_order: int = 0


class BodyRawItem(BaseModel):
    content: Optional[str] = ""


class AssertionItem(BaseModel):
    assertion_type: str  # status_code / response_time / jsonpath / header / body_contains
    operator: str  # equals / not_equals / contains / greater_than / less_than / regex / exists
    field: Optional[str] = ""
    expected: Optional[str] = ""
    description: Optional[str] = ""
    sort_order: int = 0


class ExtractItem(BaseModel):
    name: str
    source: str  # jsonpath / regex / header
    expression: str
    default_value: Optional[str] = ""
    description: Optional[str] = ""
    sort_order: int = 0


class AuthConfig(BaseModel):
    auth_type: str = "none"  # none / bearer / basic / api_key
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key_name: Optional[str] = None
    api_key_value: Optional[str] = None
    api_key_location: Optional[str] = None  # header / query


# ============================================================
# 用例主表 Schemas
# ============================================================

class APITestCaseCreate(BaseModel):
    project_id: int
    module: Optional[str] = None
    name: str
    description: Optional[str] = None
    preconditions: Optional[str] = None
    remark: Optional[str] = None

    method: str = "GET"
    url: str = ""
    body_type: str = "none"  # none / form-data / x-www-form-urlencoded / raw-json / raw-xml / raw-text
    auth_type: str = "none"

    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None

    tags: list[str] = []
    priority: str = "P2"  # P0 / P1 / P2 / P3
    status: str = "draft"  # draft / reviewed / deprecated

    # 嵌套子表数据
    headers: list[HeaderItem] = []
    query_params: list[QueryParamItem] = []
    body_form: list[BodyFormItem] = []
    body_raw: Optional[BodyRawItem] = None
    assertions: list[AssertionItem] = []
    extracts: list[ExtractItem] = []
    auth: Optional[AuthConfig] = None


class APITestCaseUpdate(BaseModel):
    module: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    preconditions: Optional[str] = None
    remark: Optional[str] = None

    method: Optional[str] = None
    url: Optional[str] = None
    body_type: Optional[str] = None
    auth_type: Optional[str] = None

    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None

    tags: Optional[list[str]] = None
    priority: Optional[str] = None
    status: Optional[str] = None

    headers: Optional[list[HeaderItem]] = None
    query_params: Optional[list[QueryParamItem]] = None
    body_form: Optional[list[BodyFormItem]] = None
    body_raw: Optional[BodyRawItem] = None
    assertions: Optional[list[AssertionItem]] = None
    extracts: Optional[list[ExtractItem]] = None
    auth: Optional[AuthConfig] = None


class APITestCaseInDB(BaseModel):
    id: int
    project_id: int
    case_number: Optional[str] = None
    module: Optional[str] = None
    name: str
    description: Optional[str] = None
    preconditions: Optional[str] = None
    remark: Optional[str] = None

    method: str
    url: str
    body_type: str = "none"
    auth_type: str = "none"

    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None

    tags: list[str] = []
    priority: str = "P2"
    status: str = "draft"

    version: int = 1
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 嵌套子表
    headers: list[HeaderItem] = []
    query_params: list[QueryParamItem] = []
    body_form: list[BodyFormItem] = []
    body_raw: Optional[BodyRawItem] = None
    assertions: list[AssertionItem] = []
    extracts: list[ExtractItem] = []
    auth: Optional[AuthConfig] = None

    class Config:
        from_attributes = True


# ============================================================
# 历史记录 Schemas
# ============================================================

class APITestCaseHistoryBase(BaseModel):
    version: int
    snapshot: dict
    change_description: Optional[str] = None


class APITestCaseHistoryInDB(APITestCaseHistoryBase):
    id: int
    test_case_id: int
    changed_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 批量操作 Schemas
# ============================================================

class BatchTagRequest(BaseModel):
    case_ids: list[int]
    tags: list[str]
    operation: str = "add"  # add / remove


class BatchDeleteRequest(BaseModel):
    case_ids: list[int]


class CreateModuleRequest(BaseModel):
    project_id: int
    module: str


class RenameModuleRequest(BaseModel):
    project_id: int
    old_module: str
    new_module: str


# ============================================================
# cURL导入 Schemas
# ============================================================

class CurlImportRequest(BaseModel):
    curl_command: str


# ============================================================
# 环境 Schemas
# ============================================================

class EnvironmentBase(BaseModel):
    name: str
    base_url: Optional[str] = None
    variables: dict = {}


class EnvironmentCreate(EnvironmentBase):
    project_id: int


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    variables: Optional[dict] = None


class EnvironmentInDB(EnvironmentBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
