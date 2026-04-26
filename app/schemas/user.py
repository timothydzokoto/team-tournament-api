from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    coach = "coach"
    viewer = "viewer"


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserRegister(UserBase):
    """Public registration — role is always defaulted to coach server-side."""
    password: str


class UserCreate(UserBase):
    """Admin-only user creation — role can be specified."""
    password: str
    role: UserRole = UserRole.coach


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    username: Optional[str] = None
