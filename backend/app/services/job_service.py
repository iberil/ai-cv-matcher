from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.job_posting import JobPosting
from ..schemas.job_schema import JobPostingCreate
import json
import logging

def create_job(db: Session, job: JobPostingCreate, user_id: int, features: dict = None) -> JobPosting:
    """İş ilanı oluştur"""
    job_data = job.dict()
    
    db_job = JobPosting(
        **job_data,
        created_by=user_id,
        education_requirements=json.dumps(features.get('education_requirements', [])) if features else None,
        required_skills_analysis=json.dumps(features.get('required_skills', {})) if features else None,
        is_mandatory_education=features.get('is_mandatory_education', False) if features else False,
        job_category=features.get('job_category', 'other') if features else 'other',
        features_extracted=bool(features)
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job

def get_job_by_id(db: Session, job_id: int) -> Optional[JobPosting]:
    """ID'ye göre iş ilanı getir"""
    return db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.is_active == True
    ).first()

def get_all_jobs(db: Session, skip: int = 0, limit: int = 20) -> List[JobPosting]:
    """Tüm aktif iş ilanlarını getir"""
    return db.query(JobPosting).filter(
        JobPosting.is_active == True
    ).offset(skip).limit(limit).all()

def get_user_jobs(db: Session, user_id: int) -> List[JobPosting]:
    """Kullanıcının iş ilanlarını getir"""
    return db.query(JobPosting).filter(
        JobPosting.created_by == user_id
    ).all()

def update_job(db: Session, job_id: int, job_update: dict) -> Optional[JobPosting]:
    """İş ilanını güncelle"""
    db_job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not db_job:
        return None
    
    for key, value in job_update.items():
        if hasattr(db_job, key) and value is not None:
            setattr(db_job, key, value)
    
    db.commit()
    db.refresh(db_job)
    
    return db_job

def delete_job(db: Session, job_id: int) -> bool:
    """İş ilanını sil (soft delete)"""
    db_job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not db_job:
        return False
    
    db_job.is_active = False
    db.commit()
    
    return True
