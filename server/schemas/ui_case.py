from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UIStepBase(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None


class UICaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list[dict] = []
    locators: dict = {}
    assertions: list[dict] = []


class UICaseCreate(UICaseBase):
    project_id: int


class UICaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list[dict]] = None
    locators: Optional[dict] = None
    assertions: Optional[list[dict]] = None


class UICaseInDB(UICaseBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
