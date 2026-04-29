from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from models.api_case import HTTPMethod


class APICaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    method: HTTPMethod
    url: str
    headers: dict = {}
    query_params: dict = {}
    body: Optional[str] = None
    body_type: str = "json"
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    assertions: list[dict] = []
    extract_vars: dict = {}


class APICaseCreate(APICaseBase):
    project_id: int


class APICaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[HTTPMethod] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    query_params: Optional[dict] = None
    body: Optional[str] = None
    body_type: Optional[str] = None
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    assertions: Optional[list[dict]] = None
    extract_vars: Optional[dict] = None


class APICaseInDB(APICaseBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIDebugRequest(BaseModel):
    method: HTTPMethod
    url: str
    headers: dict = {}
    query_params: dict = {}
    body: Optional[str] = None
    body_type: str = "json"
