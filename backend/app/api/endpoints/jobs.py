from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import logging

from ...core.database import get_db
from ...models import JobPosting, User
from ...schemas.job_schema import JobPostingCreate, JobPostingRead, JobPostingUpdate
from ...schemas.analysis_schema import CompetitorAnalysisResponse
from ...services.job_analysis_service import job_analyzer
from ...services import job_service
from ...services.analysis_service import generate_competitor_analysis
from .auth import get_current_active_user

router = APIRouter()

@router.post("/admin", response_model=JobPostingRead)
def create_job_admin(
    job: JobPostingCreate,
    db: Session = Depends(get_db)
):
    """Admin için hızlı iş ilanı ekleme (auth bypass)"""
    
    job_data = job.dict()
    
    try:
        # Özellik çıkarımı yap
        features = job_analyzer.extract_job_features(job_data)
        
        # Extracted skills'i skills_required alanına doldur (eğer yoksa)
        if not job_data.get('skills_required'):
            req_skills = features.get('required_skills', {})
            tech = req_skills.get('technical_skills', []) if isinstance(req_skills, dict) else []
            soft = req_skills.get('soft_skills', []) if isinstance(req_skills, dict) else []
            job_data['skills_required'] = ", ".join(tech + soft)
            
        db_job = JobPosting(
            **job_data,
            education_requirements=json.dumps(features.get('education_requirements', [])),
            required_skills_analysis=json.dumps(features.get('required_skills', {})),
            is_mandatory_education=features.get('is_mandatory_education', False),
            job_category=features.get('job_category', 'other'),
            features_extracted=True
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return db_job
        
    except Exception as e:
        db.rollback()
        
        db_job = JobPosting(
            **job_data,
            features_extracted=False
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return db_job

@router.post("/", response_model=JobPostingRead)
def create_job_posting(
    job: JobPostingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanı oluştur (sadece iş verenler) - Otomatik özellik çıkarımı ile"""
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece iş verenler ilan oluşturabilir"
        )
    
    # İş ilanı verilerini hazırla
    job_data = job.dict()
    
    try:
        # Özellik çıkarımı yap
        features = job_analyzer.extract_job_features(job_data)
        logging.info(f"İş ilanı özellikleri çıkarıldı: {features}")
        
        # Extracted skills'i skills_required alanına doldur (eğer yoksa)
        if not job_data.get('skills_required'):
            req_skills = features.get('required_skills', {})
            tech = req_skills.get('technical_skills', []) if isinstance(req_skills, dict) else []
            soft = req_skills.get('soft_skills', []) if isinstance(req_skills, dict) else []
            job_data['skills_required'] = ", ".join(tech + soft)
        
        # Veritabanı kaydı oluştur
        db_job = JobPosting(
            **job_data,
            created_by=current_user.id,
            education_requirements=json.dumps(features.get('education_requirements', [])),
            required_skills_analysis=json.dumps(features.get('required_skills', {})),
            is_mandatory_education=features.get('is_mandatory_education', False),
            job_category=features.get('job_category', 'other'),
            features_extracted=True
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        logging.info(f"İş ilanı oluşturuldu: ID={db_job.id}, Kategori={db_job.job_category}")
        
        return db_job
        
    except Exception as e:
        logging.error(f"İş ilanı oluşturma hatası: {e}")
        db.rollback()
        
        # Hata durumunda özellik çıkarımı olmadan kaydet
        db_job = JobPosting(
            **job_data,
            created_by=current_user.id,
            features_extracted=False
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return db_job

@router.get("/my-jobs", response_model=List[JobPostingRead])
def get_my_job_postings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Kullanıcının oluşturduğu iş ilanları"""
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece iş verenler bu endpoint'i kullanabilir"
        )
    
    jobs = db.query(JobPosting).filter(
        JobPosting.created_by == current_user.id
    ).all()
    
    return jobs

@router.get("/", response_model=List[JobPostingRead])
def get_job_postings(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Aktif iş ilanlarını listele"""
    jobs = db.query(JobPosting).filter(
        JobPosting.is_active == True
    ).offset(skip).limit(limit).all()
    
    return jobs

@router.get("/{job_id}", response_model=JobPostingRead)
def get_job_posting(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Belirli bir iş ilanını getir"""
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.is_active == True
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş ilanı bulunamadı"
        )
    
    return job

@router.put("/{job_id}", response_model=JobPostingRead)
def update_job_posting(
    job_id: int,
    job_update: JobPostingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanını güncelle (sadece oluşturan)"""
    db_job = job_service.get_job_by_id(db, job_id)
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş ilanı bulunamadı"
        )
    
    if db_job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanı güncelleme yetkiniz yok"
        )
    
    updated_job = job_service.update_job(db, job_id, job_update.dict(exclude_unset=True))
    
    return updated_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_posting(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanını sil (sadece oluşturan)"""
    db_job = job_service.get_job_by_id(db, job_id)
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş ilanı bulunamadı"
        )
    
    if db_job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanı silme yetkiniz yok"
        )
    
    job_service.delete_job(db, job_id)
    
    return None

@router.get("/{job_id}/competitor-analysis", response_model=CompetitorAnalysisResponse)
def get_competitor_analysis(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İlan rekabet analizi (sadece ilan sahibi)"""
    db_job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş ilanı bulunamadı"
        )
    
    if db_job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanın analizini görme yetkiniz yok"
        )
    
    try:
        analysis = generate_competitor_analysis(job_id, db)
        return analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logging.error(f"Analiz hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analiz sırasında bir hata oluştu"
        )