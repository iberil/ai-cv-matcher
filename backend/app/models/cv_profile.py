from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from ..core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="İsimsiz CV")
    summary = Column(Text, nullable=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    
    # ATS Compliance Fields
    ats_score = Column(Integer, nullable=True, default=None)  # 0-100 arası ATS uyumluluk skoru
    ats_compliance_level = Column(String, nullable=True, default=None)  # Mükemmel, İyi, Orta, Zayıf, Yetersiz
    ats_report = Column(JSON, nullable=True, default=None)  # Detaylı ATS raporu (JSON)
    ats_analyzed_at = Column(DateTime, nullable=True, default=None)  # ATS analiz tarihi
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    user = relationship("User", back_populates="resumes")
    experiences = relationship("Experience", back_populates="resume", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="resume", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="resume", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="resume", cascade="all, delete-orphan")

class Experience(Base):
    __tablename__ = "resume_experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    company = Column(String, nullable=True)
    position = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    resume = relationship("Resume", back_populates="experiences")

class Education(Base):
    __tablename__ = "resume_educations"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    institution = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    field = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    
    resume = relationship("Resume", back_populates="educations")

class Skill(Base):
    __tablename__ = "resume_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    
    resume = relationship("Resume", back_populates="skills")

class Language(Base):
    __tablename__ = "resume_languages"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    proficiency = Column(String, nullable=True)
    
    resume = relationship("Resume", back_populates="languages")