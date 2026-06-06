from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base
from datetime import datetime

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    skills_required = Column(Text, nullable=True)  # Virgülle ayrılmış beceriler
    location = Column(String, nullable=True)
    work_type = Column(String, nullable=True)  # remote, hybrid, office
    job_type = Column(String, nullable=True)  # full-time, part-time, contract
    experience_level = Column(String, nullable=True)  # entry, mid, senior
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    sector = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Özellik çıkarımı alanları
    education_requirements = Column(Text, nullable=True)  # JSON string
    required_skills_analysis = Column(Text, nullable=True)  # JSON string
    is_mandatory_education = Column(Boolean, default=False)
    job_category = Column(String, nullable=True)
    features_extracted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İş ilanını oluşturan kullanıcı (iş veren)
    created_by = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="job_postings")

class CVJobMatch(Base):
    __tablename__ = "cv_job_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    match_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    resume = relationship("Resume")
    job_posting = relationship("JobPosting")