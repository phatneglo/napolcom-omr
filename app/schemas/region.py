"""
Form Region schemas
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel


# Shared properties
class RegionBase(BaseModel):
    region_type: str  # 'application_number', 'answer_bubble', 'text_field', 'set_type'
    x_start: int
    y_start: int
    width: int
    height: int
    field_name: str
    properties: Optional[Dict[str, Any]] = None


# Properties to receive via API on creation
class RegionCreate(RegionBase):
    template_id: int


# Properties to receive via API on update
class RegionUpdate(RegionBase):
    region_type: Optional[str] = None
    x_start: Optional[int] = None
    y_start: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    field_name: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


# Properties to return via API
class Region(RegionBase):
    id: int
    template_id: int

    class Config:
        orm_mode = True
