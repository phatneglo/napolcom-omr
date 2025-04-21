"""
Trained Model schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class ModelBase(BaseModel):
    template_id: int
    dataset_id: int
    model_name: str
    model_path: str
    config_params: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None


# Properties to receive via API on creation
class ModelCreate(BaseModel):
    template_id: int
    dataset_id: int
    model_name: str
    training_params: Dict[str, Any]


# Properties to return via API
class Model(ModelBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Properties to return via API for list endpoint
class ModelList(BaseModel):
    items: List[Model]
    total: int
    page: int
    limit: int


# Properties to return via API for training task
class ModelTrainingTask(BaseModel):
    model_id: int
    status: str
    task_id: str
    estimated_completion_time: str


# Properties to return via API for training status
class ModelTrainingStatus(BaseModel):
    status: str
    progress: float
    current_epoch: int
    total_epochs: int
    metrics: Optional[Dict[str, Any]] = None
    eta: Optional[str] = None
