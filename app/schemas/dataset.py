"""
Training Dataset schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class DatasetBase(BaseModel):
    template_id: int
    dataset_name: str
    dataset_path: str


# Properties to receive via API on creation
class DatasetCreate(BaseModel):
    template_id: int
    dataset_name: str
    num_samples: int
    variation_params: Dict[str, Any]


# Properties to return via API
class Dataset(DatasetBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Properties to return via API for list endpoint
class DatasetList(BaseModel):
    items: List[Dataset]
    total: int
    page: int
    limit: int


# Properties to return via API for generation task
class DatasetGenerationTask(BaseModel):
    dataset_id: int
    status: str
    task_id: str
    estimated_completion_time: str
