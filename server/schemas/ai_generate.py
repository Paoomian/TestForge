from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ==================== AI 配置 Schemas ====================

class AIProviderConfigCreate(BaseModel):
    """创建 AI 配置请求"""
    model_config = ConfigDict(protected_namespaces=())

    provider: str  # claude / openai / deepseek / custom
    api_key: str
    model_name: str
    api_base_url: Optional[str] = None
    is_default: bool = False


class AIProviderConfigUpdate(BaseModel):
    """更新 AI 配置请求"""
    model_config = ConfigDict(protected_namespaces=())

    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    api_base_url: Optional[str] = None
    is_default: Optional[bool] = None


class AIProviderConfigOut(BaseModel):
    """AI 配置响应"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    user_id: int
    provider: str
    model_name: str
    api_base_url: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class AIConfigTestResult(BaseModel):
    """AI 配置测试结果"""
    success: bool
    message: str


# ==================== 生成任务 Schemas ====================

class AIGenerateTaskCreate(BaseModel):
    """创建生成任务请求"""
    project_id: Optional[int] = None  # 接口测试必须，功能测试可选
    input_type: str  # prd / swagger / text
    input_content: Optional[str] = None
    input_file_path: Optional[str] = None
    input_file_name: Optional[str] = None
    generate_type: str  # functional / api
    config_id: Optional[int] = None  # 指定使用哪个配置，不传则使用默认
    skill_id: Optional[int] = None  # 指定使用哪个技能，不传则使用默认
    target_count: int = 10


class AIGenerateTaskOut(BaseModel):
    """生成任务响应"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    user_id: int
    project_id: Optional[int] = None
    input_type: str
    input_content: Optional[str] = None
    input_file_path: Optional[str] = None
    input_file_name: Optional[str] = None
    generate_type: str
    skill_id: Optional[int] = None
    provider: str
    model_name: str
    target_count: int
    status: str
    progress: int
    error_message: Optional[str] = None
    generated_cases: Optional[List[Any]] = None
    cases_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AIGenerateTaskListOut(BaseModel):
    """生成任务列表响应（不含生成结果）"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    user_id: int
    project_id: Optional[int] = None
    input_type: str
    input_file_name: Optional[str] = None
    generate_type: str
    skill_id: Optional[int] = None
    provider: str
    model_name: str
    target_count: int
    status: str
    progress: int
    error_message: Optional[str] = None
    cases_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ==================== 文档上传响应 ====================

class DocumentUploadOut(BaseModel):
    """文档上传响应"""
    file_path: str
    file_name: str
    parsed_content: Any


# ==================== 结果操作 ====================

class SaveCasesRequest(BaseModel):
    """保存用例请求"""
    case_indices: Optional[List[int]] = None  # 不传则保存全部
    project_id: int  # 必填，目标项目


class SaveCasesResult(BaseModel):
    """保存用例结果"""
    message: str
    saved_count: int
    errors: list[str] = []


class GeneratedCaseUpdate(BaseModel):
    """更新生成的用例"""
    # 接受任意字段
    class Config:
        from_attributes = True
