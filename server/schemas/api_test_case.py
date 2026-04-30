from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class APITestCaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    module: Optional[str] = None
    method: str
    url: str
    headers: dict = {}
    body: Optional[str] = None
    query_params: dict = {}
    variables: dict = {}
    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None
    assertions: list = []
    tags: list = []
    priority: str = "medium"
    status: str = "active"


class APITestCaseCreate(APITestCaseBase):
    project_id: int


class APITestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    body: Optional[str] = None
    query_params: Optional[dict] = None
    variables: Optional[dict] = None
    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None
    assertions: Optional[list] = None
    tags: Optional[list] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class APITestCaseInDB(APITestCaseBase):
    id: int
    project_id: int
    version: int
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class BatchTagRequest(BaseModel):
    case_ids: list[int]
    tags: list[str]
    operation: str = "add"  # add or remove


class BatchDeleteRequest(BaseModel):
    case_ids: list[int]
