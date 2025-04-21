"""
User schemas
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    username: str
    email: str  # Changed from EmailStr to str for simpler validation
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


# Properties to return via API
class User(UserBase):
    id: int
    created_at: datetime
    permissions: List[Any] = []  # Changed from List[Permission] to List[Any]

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic v2


# Properties for token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Properties for refresh token
class TokenRefresh(BaseModel):
    refresh_token: str
