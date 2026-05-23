from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AISkillCreate(BaseModel):
    """创建技能请求"""
    name: str
    description: Optional[str] = ""
    generate_type: str  # functional / api
    system_prompt: str
    user_prompt: str  # 必须包含 {input_content}
    is_default: bool = False


class AISkillUpdate(BaseModel):
    """更新技能请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    generate_type: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    is_default: Optional[bool] = None


class AISkillOut(BaseModel):
    """技能响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: Optional[str] = ""
    generate_type: str
    system_prompt: str
    user_prompt: str
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
