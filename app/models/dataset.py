"""
Training Dataset model
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class TrainingDataset(Base):
    __tablename__ = "training_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("form_templates.id"), nullable=False)
    dataset_name = Column(String, nullable=False)
    dataset_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    template = relationship("FormTemplate", back_populates="datasets")
    models = relationship("TrainedModel", back_populates="dataset")
