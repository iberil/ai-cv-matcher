from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from ..core.database import Base
from datetime import datetime

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, reviewed, accepted, rejected
    cover_letter = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    job = relationship("JobPosting")
    user = relationship("User")

class FavoriteJob(Base):
    __tablename__ = "favorite_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    job = relationship("JobPosting")
    user = relationship("User")
