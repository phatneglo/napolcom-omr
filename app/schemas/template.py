"""
Form Template schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.schemas.region import Region


# Shared properties
class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None


# Properties to receive via API on creation
class TemplateCreate(TemplateBase):
    pass


# Properties to receive via API on update
class TemplateUpdate(TemplateBase):
    name: Optional[str] = None


# Properties to return via API
class Template(TemplateBase):
    id: int
    created_at: datetime
    regions: List[Region] = []

    class Config:
        orm_mode = True


# Properties to return via API for list endpoint
class TemplateList(BaseModel):
    items: List[Template]
    total: int
    page: int
    limit: int
