"""
Processed Form model
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProcessedForm(Base):
    __tablename__ = "processed_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("form_templates.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("trained_models.id"), nullable=False)
    image_path = Column(String, nullable=False)
    extracted_data = Column(JSON)
    confidence_score = Column(Float)
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    template = relationship("FormTemplate", back_populates="processed_forms")
    model = relationship("TrainedModel", back_populates="processed_forms")
