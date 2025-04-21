"""
Form Template model
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class FormTemplate(Base):
    __tablename__ = "form_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    regions = relationship("FormRegion", back_populates="template", cascade="all, delete-orphan")
    datasets = relationship("TrainingDataset", back_populates="template")
    models = relationship("TrainedModel", back_populates="template")
    processed_forms = relationship("ProcessedForm", back_populates="template")
