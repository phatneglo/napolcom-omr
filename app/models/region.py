"""
Form Region model
"""
import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class FormRegion(Base):
    __tablename__ = "form_regions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("form_templates.id"), nullable=False)
    region_type = Column(String, nullable=False)  # 'application_number', 'answer_bubble', 'text_field', 'set_type'
    x_start = Column(Integer, nullable=False)
    y_start = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    field_name = Column(String, nullable=False)
    properties = Column(JSON)  # Store specific properties for each region type
    
    # Relationships
    template = relationship("FormTemplate", back_populates="regions")
