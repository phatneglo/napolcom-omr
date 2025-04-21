"""
Trained Model model
"""
import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class TrainedModel(Base):
    __tablename__ = "trained_models"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("form_templates.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("training_datasets.id"), nullable=False)
    model_name = Column(String, nullable=False)
    model_path = Column(String, nullable=False)
    config_params = Column(JSON)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    template = relationship("FormTemplate", back_populates="models")
    dataset = relationship("TrainingDataset", back_populates="models")
    processed_forms = relationship("ProcessedForm", back_populates="model")
