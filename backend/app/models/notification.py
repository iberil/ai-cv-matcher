from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, Boolean
from sqlalchemy.orm import relationship
from ..core.database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")  # info, success, warning, error
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
