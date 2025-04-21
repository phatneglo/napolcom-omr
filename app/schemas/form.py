"""
Processed Form schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# Properties to receive via API on creation
class FormCreate(BaseModel):
    template_id: int
    model_id: int


# Properties to return via API
class Form(BaseModel):
    id: int
    template_id: int
    model_id: int
    image_path: str
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    processed_at: datetime

    class Config:
        orm_mode = True


# Properties to return via API for list endpoint
class FormList(BaseModel):
    items: List[Form]
    total: int
    page: int
    limit: int


# Properties to return via API for processing task
class FormProcessingTask(BaseModel):
    form_id: int
    status: str
    task_id: str
