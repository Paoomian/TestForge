from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: list[str] = []


class RoleCreate(RoleBase):
    pass


class RoleInDB(RoleBase):
    id: int

    class Config:
        from_attributes = True
