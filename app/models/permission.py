"""
Permission model
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="permissions")
    
    # Ensure uniqueness of user_id + permission_type
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_type'),
    )
