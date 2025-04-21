"""
Permission schemas
"""
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class PermissionBase(BaseModel):
    permission_type: str


# Properties to receive via API on creation
class PermissionCreate(PermissionBase):
    user_id: int


# Properties to return via API
class Permission(PermissionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic v2
