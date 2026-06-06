from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ...core.database import get_db
from ...models import User, JobPosting
from ...models.cv_profile import Resume
from ...services.detailed_matching_service import detailed_matching_service
from ...services.matching_service import get_matcher
from ..endpoints.auth import get_current_active_user

router = APIRouter()

@router.get("/jobs/{job_id}/candidates")
def get_job_candidates(
    job_id: int,
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İş ilanı için uygun adayları skorlarıyla birlikte getir"""
    
    # Sadece işverenler erişebilir
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece işverenler aday havuzunu görebilir"
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
            detail="Bu ilanın adaylarını görme yetkiniz yok"
        )
    
    # Tüm CV'leri getir
    resumes = db.query(Resume).join(User).filter(User.user_role == "aday").all()
    
    if not resumes:
        return {
            "job_title": job.title,
            "candidates": [],
            "total_candidates": 0,
            "message": "Henüz aday bulunamadı"
        }
    
    # İş ilanı verilerini hazırla
    job_data = {
        "title": job.title,
        "description": job.description,
        "requirements": job.requirements,
        "skills_required": job.skills_required,
        "experience_level": job.experience_level,
        "sector": job.sector
    }
    
    # Matcher'ı al
    matcher = get_matcher()
    candidates = []
    
    for resume in resumes:
        try:
            # CV verilerini hazırla
            cv_data = {
                "skills": ", ".join([skill.name for skill in resume.skills]),
                "experience": "\n".join([f"{exp.position} at {exp.company}" for exp in resume.experiences]),
                "education": "\n".join([f"{edu.degree} in {edu.field} from {edu.institution}" for edu in resume.educations]),
                "summary": resume.summary or ""
            }
            
            # CV profili oluştur ve skorla
            cv_profile = matcher.create_cv_profile(cv_data)
            job_profile = matcher.create_job_profile(job_data)
            
            # Temel skor
            base_score = matcher.calculate_similarity_score(cv_profile, job_profile)
            
            # Beceri bonusu
            cv_skills = [skill.name for skill in resume.skills]
            job_skills = job.skills_required.split(',') if job.skills_required else []
            skill_bonus = matcher.calculate_skill_match_bonus(cv_skills, job_skills)
            
            # Kritik ceza
            critical_penalty = matcher.calculate_critical_skill_penalty(cv_data, job_data)
            
            # Final skor
            if critical_penalty <= -50:
                final_score = 0.0
            else:
                final_score = max(base_score + skill_bonus + critical_penalty, 0)
                final_score = min(final_score, 100)
            
            # Minimum skoru geçiyorsa listeye ekle
            if final_score >= min_score:
                candidate_info = {
                    "candidate_id": resume.user_id,
                    "resume_id": resume.id,
                    "name": resume.user.full_name or "İsimsiz",
                    "email": resume.user.email,
                    "profession": resume.user.profession,
                    "match_score": round(final_score, 2),
                    "skills": [skill.name for skill in resume.skills],
                    "experience_count": len(resume.experiences),
                    "education_level": resume.educations[0].degree if resume.educations else "Belirtilmemiş",
                    "summary": resume.summary[:200] + "..." if resume.summary and len(resume.summary) > 200 else resume.summary
                }
                candidates.append(candidate_info)
                
        except Exception as e:
            logging.error(f"Candidate scoring error for resume {resume.id}: {e}")
            continue
    
    # Skora göre sırala
    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Limit uygula
    candidates = candidates[:limit]
    
    return {
        "job_title": job.title,
        "job_id": job_id,
        "candidates": candidates,
        "total_candidates": len(candidates),
        "filters": {
            "min_score": min_score,
            "limit": limit
        }
    }

@router.get("/jobs/{job_id}/candidates/{candidate_id}/detailed-match")
def get_detailed_candidate_match(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Aday için detaylı eşleştirme raporu"""
    
    # Sadece işverenler erişebilir
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece işverenler detaylı raporu görebilir"
        )
    
    # İş ilanının sahibi mi kontrol et
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job or job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanın detaylı raporunu görme yetkiniz yok"
        )
    
    # Adayı getir
    candidate = db.query(User).filter(
        User.id == candidate_id,
        User.user_role == "aday"
    ).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aday bulunamadı"
        )
    
    # Adayın CV'sini getir
    resume = db.query(Resume).filter(Resume.user_id == candidate_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adayın CV'si bulunamadı"
        )
    
    # Veri hazırlama
    cv_data = {
        "skills": ", ".join([skill.name for skill in resume.skills]),
        "experience": "\n".join([
            f"{exp.position} at {exp.company} ({exp.start_date} - {exp.end_date}): {exp.description or ''}"
            for exp in resume.experiences
        ]),
        "education": "\n".join([
            f"{edu.degree} in {edu.field} from {edu.institution} ({edu.start_date} - {edu.end_date})"
            for edu in resume.educations
        ]),
        "summary": resume.summary or ""
    }
    
    job_data = {
        "title": job.title,
        "description": job.description,
        "requirements": job.requirements,
        "skills_required": job.skills_required,
        "experience_level": job.experience_level,
        "sector": job.sector,
        "work_type": job.work_type,
        "job_type": job.job_type
    }
    
    # Detaylı analiz yap
    detailed_analysis = detailed_matching_service.analyze_candidate_job_match(cv_data, job_data)
    
    # Aday bilgilerini ekle
    candidate_info = {
        "id": candidate.id,
        "name": candidate.full_name or "İsimsiz",
        "email": candidate.email,
        "profession": candidate.profession,
        "date_of_birth": candidate.date_of_birth.isoformat() if candidate.date_of_birth else None
    }
    
    # CV detaylarını ekle
    cv_details = {
        "id": resume.id,
        "title": resume.title,
        "summary": resume.summary,
        "skills": [{"name": skill.name} for skill in resume.skills],
        "experiences": [
            {
                "company": exp.company,
                "position": exp.position,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "description": exp.description
            }
            for exp in resume.experiences
        ],
        "educations": [
            {
                "institution": edu.institution,
                "degree": edu.degree,
                "field": edu.field,
                "start_date": edu.start_date,
                "end_date": edu.end_date
            }
            for edu in resume.educations
        ]
    }
    
    return {
        "candidate": candidate_info,
        "cv_details": cv_details,
        "job_info": {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name
        },
        "match_analysis": detailed_analysis
    }

@router.get("/candidates/search")
def search_candidates(
    skills: Optional[str] = Query(None, description="Aranan beceriler (virgülle ayrılmış)"),
    experience_level: Optional[str] = Query(None, description="Deneyim seviyesi"),
    education_field: Optional[str] = Query(None, description="Eğitim alanı"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Genel aday arama (tüm işverenler için)"""
    
    if current_user.user_role != "isveren":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece işverenler aday arayabilir"
        )
    
    # Base query
    query = db.query(Resume).join(User).filter(User.user_role == "aday")
    
    # Filtreleme
    if skills:
        skill_list = [s.strip().lower() for s in skills.split(',')]
        # Bu kısım daha karmaşık bir filtreleme gerektirir, şimdilik basit tutuyoruz
        pass
    
    resumes = query.limit(limit).all()
    
    candidates = []
    for resume in resumes:
        candidate_info = {
            "candidate_id": resume.user_id,
            "resume_id": resume.id,
            "name": resume.user.full_name or "İsimsiz",
            "email": resume.user.email,
            "profession": resume.user.profession,
            "skills": [skill.name for skill in resume.skills],
            "experience_count": len(resume.experiences),
            "education_level": resume.educations[0].degree if resume.educations else "Belirtilmemiş",
            "summary": resume.summary[:200] + "..." if resume.summary and len(resume.summary) > 200 else resume.summary
        }
        candidates.append(candidate_info)
    
    return {
        "candidates": candidates,
        "total": len(candidates),
        "filters": {
            "skills": skills,
            "experience_level": experience_level,
            "education_field": education_field
        }
    }