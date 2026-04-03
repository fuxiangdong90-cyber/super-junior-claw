"""用户Schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, UserStatus


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    tenant_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    role: UserRole
    status: UserStatus
    is_active: bool
    is_superuser: bool
    tenant_id: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Tenant Schemas
class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_concurrent_tasks: Optional[int] = None
    max_storage_gb: Optional[int] = None
    subscription_type: Optional[str] = None


class TenantResponse(TenantBase):
    id: str
    status: UserStatus
    max_concurrent_tasks: int
    max_storage_gb: int
    used_concurrent_tasks: int
    used_storage_gb: int
    balance: int
    subscription_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True