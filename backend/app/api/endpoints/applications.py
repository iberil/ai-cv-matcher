from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.application import JobApplication, FavoriteJob
from ...models import User, JobPosting
from ...models.cv_profile import Resume
from ...schemas.application_schema import ApplicationWithCandidate, ApplicationStatusUpdate
from ..endpoints.auth import get_current_active_user
from ...services.notification_service import create_notification

router = APIRouter()

@router.post("/jobs/{job_id}/apply")
def apply_to_job(
    job_id: int,
    cover_letter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanına başvur"""
    if current_user.user_role != "aday":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece adaylar başvurabilir"
        )
    
    # Daha önce başvurmuş mu kontrol et
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ilana zaten başvurdunuz"
        )
    
    application = JobApplication(
        job_id=job_id,
        user_id=current_user.id,
        cover_letter=cover_letter
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    return {"message": "Başvurunuz alındı", "application_id": application.id}

@router.post("/jobs/{job_id}/favorite")
def add_to_favorites(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanını favorilere ekle"""
    if current_user.user_role != "aday":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece adaylar favori ekleyebilir"
        )
    
    # Zaten favoride mi kontrol et
    existing = db.query(FavoriteJob).filter(
        FavoriteJob.job_id == job_id,
        FavoriteJob.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ilan zaten favorilerinizde"
        )
    
    favorite = FavoriteJob(
        job_id=job_id,
        user_id=current_user.id
    )
    
    db.add(favorite)
    db.commit()
    
    return {"message": "Favorilere eklendi"}

@router.delete("/jobs/{job_id}/favorite")
def remove_from_favorites(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanını favorilerden çıkar"""
    favorite = db.query(FavoriteJob).filter(
        FavoriteJob.job_id == job_id,
        FavoriteJob.user_id == current_user.id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu ilan favorilerinizde değil"
        )
    
    db.delete(favorite)
    db.commit()
    
    return {"message": "Favorilerden çıkarıldı"}

@router.get("/jobs/{job_id}/check-status")
def check_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanı için başvuru ve favori durumunu kontrol et"""
    has_applied = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.user_id == current_user.id
    ).first() is not None
    
    is_favorite = db.query(FavoriteJob).filter(
        FavoriteJob.job_id == job_id,
        FavoriteJob.user_id == current_user.id
    ).first() is not None
    
    return {
        "has_applied": has_applied,
        "is_favorite": is_favorite
    }

@router.get("/my-favorites")
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Kullanıcının favori iş ilanlarını getir"""
    favorites = db.query(FavoriteJob).filter(
        FavoriteJob.user_id == current_user.id
    ).all()
    
    jobs = []
    for fav in favorites:
        job = fav.job
        if job and job.is_active:
            jobs.append({
                "id": job.id,
                "title": job.title,
                "company_name": job.company_name,
                "location": job.location,
                "work_type": job.work_type,
                "job_type": job.job_type,
                "created_at": job.created_at,
                "favorited_at": fav.created_at
            })
    
    return {"favorites": jobs, "total": len(jobs)}

@router.get("/jobs/{job_id}/applications", response_model=List[ApplicationWithCandidate])
def get_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanına yapılan başvuruları getir (sadece iş veren)"""
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece iş verenler başvuruları görebilir"
        )
    
    # İş ilanının sahibi mi kontrol et
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş ilanı bulunamadı"
        )
    
    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanın başvurularını görme yetkiniz yok"
        )
    
    # Başvuruları getir
    applications = db.query(JobApplication).filter(
        JobApplication.job_id == job_id
    ).all()
    
    result = []
    for app in applications:
        candidate = app.user
        resume = db.query(Resume).filter(Resume.user_id == candidate.id).first()
        
        result.append(ApplicationWithCandidate(
            id=app.id,
            job_id=app.job_id,
            status=app.status,
            cover_letter=app.cover_letter,
            applied_at=app.applied_at,
            candidate_name=candidate.full_name or "İsimsiz",
            candidate_email=candidate.email,
            candidate_phone=resume.phone if resume else None,
            candidate_profession=candidate.profession
        ))
    
    return result

@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Başvuru durumunu güncelle (sadece iş veren)"""
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece iş verenler başvuru durumunu güncelleyebilir"
        )
    
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Başvuru bulunamadı"
        )
    
    # İş ilanının sahibi mi kontrol et
    job = db.query(JobPosting).filter(JobPosting.id == application.job_id).first()
    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu başvuruyu güncelleme yetkiniz yok"
        )
    
    # Durumu güncelle
    old_status = application.status
    application.status = status_update.status
    db.commit()
    
    # Adaya bildirim gönder
    if old_status != status_update.status:
        status_messages = {
            "reviewed": f"{job.title} pozisyonuna yaptığınız başvuru incelendi.",
            "accepted": f"Tebrikler! {job.title} pozisyonuna başvurunuz kabul edildi.",
            "rejected": f"{job.title} pozisyonuna yaptığınız başvuru maalesef reddedildi."
        }
        
        if status_update.status in status_messages:
            notification_type = "success" if status_update.status == "accepted" else "info" if status_update.status == "reviewed" else "warning"
            create_notification(
                db=db,
                user_id=application.user_id,
                title="Başvuru Durumu Güncellendi",
                message=status_messages[status_update.status],
                type=notification_type
            )
    
    return {"message": "Başvuru durumu güncellendi", "status": application.status}

@router.get("/my-applications")
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Kullanıcının yaptığı başvuruları getir (aday için)"""
    if current_user.user_role != "aday":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece adaylar başvurularını görebilir"
        )
    
    applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    result = []
    for app in applications:
        job = app.job
        if job:
            result.append({
                "id": app.id,
                "status": app.status,
                "applied_at": app.applied_at,
                "job_title": job.title,
                "company_name": job.company_name,
                "job_location": job.location,
                "job_type": job.job_type
            })
    
    return {"applications": result, "total": len(result)}
