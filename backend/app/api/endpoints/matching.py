from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import time
import logging

from ...core.database import get_db
from ...models.user import User
from ...models.job_posting import JobPosting, CVJobMatch
from ...models.application import JobApplication
from ...models.cv_profile import Resume
from ...schemas.job_schema import (
    JobMatchRequest, 
    JobMatchResponse,
    JobPostingWithScore
)
from ...services.matching_service import get_matcher
from ...services.detailed_matching_service import detailed_matching_service
from .auth import get_current_active_user

router = APIRouter()

@router.post("/match-jobs", response_model=JobMatchResponse)
def match_jobs_with_cv(
    request: JobMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Kullanıcının CV'si ile iş ilanlarını otomatik eşleştir"""
    start_time = time.time()
    
    # Kullanıcının en son CV'sini al
    resume = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).first()
    
    if not resume:
        # Kullanıcının hiç CV'si yok
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Henüz kaydedilmiş CV bulunamadı. Lütfen Profil sayfasından CV yükleyin ve 'Kaydet' butonuna tıklayın."
        )
    
    # Kullanıcının kendi CV'si mi kontrol et (otomatik seçim olduğu için bu kontrol gereksiz)
    # if resume.user_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Bu CV'ye erişim yetkiniz yok"
    #     )
    
    # Aktif iş ilanlarını getir
    jobs = db.query(JobPosting).filter(
        JobPosting.is_active == True
    ).all()
    
    if not jobs:
        return JobMatchResponse(
            matches=[],
            total_jobs=0,
            processing_time=time.time() - start_time
        )
    
    # CV verisini hazırla
    skills_text = ', '.join([skill.name for skill in resume.skills])
    
    # Deneyim metnini tarihlerle birlikte oluştur
    experience_parts = []
    for exp in resume.experiences:
        exp_text = f"{exp.position} at {exp.company}"
        if exp.start_date or exp.end_date:
            date_range = f" ({exp.start_date or '?'} - {exp.end_date or 'Present'})"
            exp_text += date_range
        if exp.description:
            exp_text += f": {exp.description}"
        experience_parts.append(exp_text)
    experience_text = ' '.join(experience_parts)
    
    education_text = ' '.join([f"{edu.degree} in {edu.field or ''} from {edu.institution}" for edu in resume.educations])
    
    cv_data = {
        'skills': skills_text,
        'experience': experience_text,
        'education': education_text,
        'summary': resume.summary or ''
    }
    
    # İş ilanı verilerini hazırla
    jobs_data = []
    for job in jobs:
        job_data = {
            'id': job.id,
            'title': job.title,
            'company_name': job.company_name,
            'description': job.description,
            'requirements': job.requirements,
            'skills_required': job.skills_required,
            'location': job.location,
            'work_type': job.work_type,
            'job_type': job.job_type,
            'experience_level': job.experience_level,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'sector': job.sector,
            'is_active': job.is_active,
            'created_at': job.created_at,
            'created_by': job.created_by
        }
        jobs_data.append(job_data)
    
    # Eşleştirme yap
    matcher = get_matcher()
    
    # Tüm ilanları eşleştirmek için sadece base score'ları hesapla
    base_scores = matcher.match_cv_with_jobs_base_scores(cv_data, jobs_data)
    
    # Detaylı skor hesabı yap
    all_matches = []
    for job_data in jobs_data:
        job_id = job_data['id']
        base_score = base_scores.get(job_id, 0.0)
        
        analysis = detailed_matching_service.analyze_candidate_job_match(
            cv_data, job_data, precomputed_base_score=base_score
        )
        final_score = analysis['overall_score']
        all_matches.append((job_data, final_score))
        
    # Skora göre sırala (yüksekten düşüğe)
    all_matches.sort(key=lambda x: x[1], reverse=True)
    
    # Debug: İlk 10 skoru logla
    print(f"DEBUG: Total jobs matched: {len(all_matches)}")
    for job_data, score in all_matches[:10]:
        print(f"  - {job_data.get('title')} ({job_data.get('company_name')}): {score}")
    
    # Limit uygula
    top_matches_tuples = all_matches[:request.limit]
    
    # Sonuçları formatla
    matches = []
    for job_data, score in top_matches_tuples:
        job_with_score = job_data.copy()
        job_with_score['match_score'] = round(score, 2)
        match = JobPostingWithScore(**job_with_score)
        matches.append(match)
    
    processing_time = time.time() - start_time
    
    return JobMatchResponse(
        matches=matches,
        total_jobs=len(jobs),
        processing_time=round(processing_time, 3)
    )

@router.get("/jobs/{job_id}/matches")
def get_candidates_for_job(
    job_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İşveren için: Belirli bir iş ilanına uygun adayları getir"""
    start_time = time.time()
    
    # İş ilanını kontrol et
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş ilanı bulunamadı"
        )
    
    # Sadece ilan sahibi erişebilir
    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilana ait aday listesini görme yetkiniz yok"
        )
    
    # Sadece BU İLANA BAŞVURAN adayların CV'lerini getir
    resumes = db.query(Resume).join(
        JobApplication, Resume.user_id == JobApplication.user_id
    ).filter(
        JobApplication.job_id == job_id
    ).all()
    
    if not resumes:
        return {
            "candidates": [],
            "total_candidates": 0,
            "processing_time": time.time() - start_time
        }
    
    # İş ilanı verisini hazırla
    job_data = {
        'id': job.id,
        'title': job.title,
        'company_name': job.company_name,
        'description': job.description,
        'requirements': job.requirements,
        'skills_required': job.skills_required,
        'location': job.location,
        'work_type': job.work_type,
        'job_type': job.job_type,
        'experience_level': job.experience_level,
        'salary_min': job.salary_min,
        'salary_max': job.salary_max,
        'sector': job.sector
    }
    
    # Her aday için verileri hazırla
    matcher = get_matcher()
    candidates = []
    cvs_data = []
    
    for resume in resumes:
        try:
            # CV verisini hazırla
            skills_text = ', '.join([skill.name for skill in resume.skills])
            
            # Deneyim metnini tarihlerle birlikte oluştur
            experience_parts = []
            for exp in resume.experiences:
                exp_text = f"{exp.position} at {exp.company}"
                if exp.start_date or exp.end_date:
                    date_range = f" ({exp.start_date or '?'} - {exp.end_date or 'Present'})"
                    exp_text += date_range
                if exp.description:
                    exp_text += f": {exp.description}"
                experience_parts.append(exp_text)
            experience_text = ' '.join(experience_parts)
            
            education_text = ' '.join([f"{edu.degree} in {edu.field or ''} from {edu.institution}" for edu in resume.educations])
            
            cv_data = {
                'id': resume.id,
                'user_id': resume.user_id,
                'skills': skills_text,
                'experience': experience_text,
                'education': education_text,
                'summary': resume.summary or '',
                'experience_count': len(resume.experiences),
                'education_short': education_text[:100] + "..." if len(education_text) > 100 else education_text,
                'created_at': resume.created_at
            }
            cvs_data.append(cv_data)
        except Exception as e:
            logging.error(f"Eksik profil verisi sebebiyle atlandı (CV ID: {resume.id}): {e}")
            continue
            
    # Tek iş ilanı ile tüm CV'leri topluca eşleştir (Optimize Edilmiş, sadece anlamsal skorlar)
    base_scores = matcher.match_job_with_cvs_base_scores(job_data, cvs_data)
    
    for cv_data in cvs_data:
        try:
            cv_id = cv_data['id']
            base_score = base_scores.get(cv_id, 0.0)
            
            # Detaylı eşleştirme motorunu kullanarak final skoru hesapla
            analysis = detailed_matching_service.analyze_candidate_job_match(
                cv_data, job_data, precomputed_base_score=base_score
            )
            final_score = analysis['overall_score']
            
            # Kullanıcı bilgilerini al
            user = db.query(User).filter(User.id == cv_data['user_id']).first()
            
            candidate_info = {
                "id": cv_id,
                "user_id": cv_data['user_id'],
                "full_name": user.full_name if user else "Bilinmiyor",
                "email": user.email if user else "",
                "match_score": final_score,
                "skills": cv_data['skills'],
                "experience_years": cv_data['experience_count'],
                "education": cv_data['education_short'],
                "created_at": cv_data['created_at']
            }
            
            candidates.append(candidate_info)
        
        except Exception as e:
            logging.error(f"Error mapping matched resume {cv_data.get('id')}: {e}")
            continue
    
    # Skora göre sırala ve Limit uygula
    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    top_candidates = candidates[:limit]
    
    processing_time = time.time() - start_time
    
    return {
        "candidates": top_candidates,
        "total_candidates": len(resumes),
        "matched_candidates": len(candidates),
        "processing_time": round(processing_time, 3)
    }


@router.get("/matches/{job_id}/{resume_id}")
def get_detailed_match(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """İşveren için: Belirli bir iş ilanı ve CV arasındaki detaylı eşleşme raporu"""
    
    # İş ilanını kontrol et
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İş ilanı bulunamadı")
    
    # Sadece ilan sahibi erişebilir
    if job.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu rapora erişim yetkiniz yok")
    
    # CV'yi getir
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV bulunamadı")
    
    # Aday kullanıcı bilgisi
    candidate_user = db.query(User).filter(User.id == resume.user_id).first()
    
    # CV verisini hazırla
    skills_text = ', '.join([skill.name for skill in resume.skills])
    
    # Deneyim metnini tarihlerle birlikte oluştur
    experience_parts = []
    for exp in resume.experiences:
        exp_text = f"{exp.position} at {exp.company}"
        if exp.start_date or exp.end_date:
            date_range = f" ({exp.start_date or '?'} - {exp.end_date or 'Present'})"
            exp_text += date_range
        if exp.description:
            exp_text += f": {exp.description}"
        experience_parts.append(exp_text)
    experience_text = ' '.join(experience_parts)
    
    education_text = ' '.join([
        f"{edu.degree} in {edu.field or ''} from {edu.institution}"
        for edu in resume.educations
    ])
    
    cv_data = {
        'skills': skills_text,
        'experience': experience_text,
        'education': education_text,
        'summary': resume.summary or ''
    }
    
    # İş ilanı verisini hazırla
    job_data = {
        'id': job.id,
        'title': job.title,
        'company_name': job.company_name,
        'description': job.description,
        'requirements': job.requirements,
        'skills_required': job.skills_required,
        'experience_level': job.experience_level,
        'location': job.location,
        'work_type': job.work_type,
        'job_type': job.job_type,
        'sector': job.sector
    }
    
    # Detaylı analiz yap
    analysis = detailed_matching_service.analyze_candidate_job_match(cv_data, job_data)
    
    return {
        "job": {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "experience_level": job.experience_level,
            "skills_required": job.skills_required
        },
        "candidate": {
            "resume_id": resume.id,
            "full_name": candidate_user.full_name if candidate_user else "Bilinmiyor",
            "email": candidate_user.email if candidate_user else "",
            "skills": skills_text,
            "experience_count": len(resume.experiences),
            "education": education_text
        },
        "analysis": analysis
    }