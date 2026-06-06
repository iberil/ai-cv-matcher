from sqlalchemy import Column, Integer, String, Boolean, Date, Text
from sqlalchemy.orm import relationship
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    date_of_birth = Column(Date, nullable=True) 
    profession = Column(String, nullable=True) 
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    user_role = Column(String, default="aday")
    
    # Şirket bilgileri (işverenler için)
    company_description = Column(Text, nullable=True)
    company_website = Column(String, nullable=True)
    company_size = Column(String, nullable=True)
    company_sector = Column(String, nullable=True)
    company_location = Column(String, nullable=True)
    
    # İlişkiler
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_postings = relationship("JobPosting", back_populates="creator")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete-orphan")