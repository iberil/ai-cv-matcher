from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import asyncio
from functools import partial
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...schemas.cv_schema import ResumeExtractResponse
from ...services.cv_service import save_temp_file, extract_features, cleanup_file, save_resume_to_db, delete_user_cv
from ...api.endpoints.auth import get_current_user
from ...models.user import User

router = APIRouter()

@router.post("/upload-and-analyze", response_model=ResumeExtractResponse)
async def upload_and_analyze_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    PDF yükle → Analiz et → JSON döndür (KAYDETME!)
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir")
    
    temp_path = save_temp_file(file, file.filename)
    
    try:
        # Gemini blocking HTTP call'unu thread pool'da calistir
        loop = asyncio.get_event_loop()
        extracted_data = await loop.run_in_executor(None, extract_features, temp_path)
        
        if not extracted_data:
            raise HTTPException(status_code=400, detail="PDF'den veri çıkarılamadı")
            
        import os, shutil, uuid
        os.makedirs("uploads", exist_ok=True)
        permanent_name = f"{current_user.id}_{uuid.uuid4().hex}_{file.filename}"
        permanent_path = os.path.join("uploads", permanent_name)
        shutil.copy2(temp_path, permanent_path)
        extracted_data['file_path'] = permanent_path
        
        resume_response = ResumeExtractResponse(**extracted_data)
        # KAYDETME - sadece analiz sonucu döndür
        print(f"DEBUG: CV analiz edildi - User: {current_user.id}, kayıt yapılmadı")
        
        return resume_response
    
    finally:
        cleanup_file(temp_path)

@router.post("/confirm-and-save")
async def confirm_and_save_cv(
    resume_data: ResumeExtractResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ONAY: Kullanıcı düzeltmeleri onayladı → DB'ye kaydet
    """
    try:
        print(f"DEBUG: Saving CV for user {current_user.id}")
        print(f"DEBUG: Resume data keys: {list(resume_data.dict().keys())}")
        
        saved_resume = save_resume_to_db(db, current_user.id, resume_data, file_path=resume_data.file_path)
        
        print(f"DEBUG: CV saved successfully with ID: {saved_resume.id}")
        
        return {
            "message": "CV başarıyla kaydedildi",
            "resume_id": saved_resume.id,
            "resume_title": saved_resume.title or "CV"
        }
    except Exception as e:
        print(f"CRITICAL ERROR in confirm_and_save_cv: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"CV kaydedilemedi: {str(e)}")

@router.get("/my-resumes")
async def get_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcının tüm CV'lerini listele (detaylı bilgilerle)
    """
    from ...models.cv_profile import Resume
    
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    
    # Her CV için detaylı bilgileri hazırla
    detailed_resumes = []
    for resume in resumes:
        resume_data = {
            "id": resume.id,
            "user_id": resume.user_id,
            "title": resume.title,
            "full_name": resume.full_name,
            "email": resume.email,
            "phone": resume.phone,
            "summary": resume.summary,
            "file_path": resume.file_path,
            "created_at": resume.created_at,
            "skills": [skill.name for skill in resume.skills],
            "languages": [lang.name for lang in resume.languages],
            "experiences": [
                {
                    "company": exp.company,
                    "position": exp.position,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "description": exp.description
                } for exp in resume.experiences
            ],
            "educations": [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field": edu.field,
                    "start_date": edu.start_date,
                    "end_date": edu.end_date
                } for edu in resume.educations
            ]
        }
        detailed_resumes.append(resume_data)
    
    return detailed_resumes

@router.get("/resume/{resume_id}/details")
async def get_resume_details(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Belirli bir CV'nin tüm detaylarını getir
    """
    from ...models.cv_profile import Resume
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="CV bulunamadı")
    
    return {
        "resume": resume,
        "skills": [s.name for s in resume.skills],
        "languages": [l.name for l in resume.languages],
        "experiences": [
            {
                "company": e.company,
                "position": e.position,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "description": e.description
            } for e in resume.experiences
        ],
        "educations": [
            {
                "institution": e.institution,
                "degree": e.degree,
                "field": e.field,
                "start_date": e.start_date,
                "end_date": e.end_date
            } for e in resume.educations
        ]
    }

@router.get("/resume/{resume_id}/pdf")
async def get_resume_pdf(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ...models.cv_profile import Resume
    from fastapi.responses import FileResponse
    import os

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume or not resume.file_path:
        raise HTTPException(status_code=404, detail="PDF bulunamadı")

    if not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Dosya sunucuda mevcut değil")

    return FileResponse(
        resume.file_path, 
        media_type="application/pdf", 
        filename=os.path.basename(resume.file_path)
    )

@router.delete("/resume/{resume_id}")
async def delete_cv(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    CV'yi ve ilişkili tüm verileri sil
    """
    success = delete_user_cv(db, resume_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="CV bulunamadı veya silinemedi")
        
    return {"message": "CV başarıyla silindi"}

@router.put("/resume/{resume_id}")
async def update_cv(
    resume_id: int,
    resume_data: ResumeExtractResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mevcut CV'yi güncelle
    """
    from ...models.cv_profile import Resume, Skill, Language, Experience, Education
    
    # CV'yi bul
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="CV bulunamadı")
    
    try:
        # Temel bilgileri güncelle
        resume.full_name = resume_data.full_name
        resume.email = resume_data.email
        resume.phone = resume_data.phone
        resume.summary = resume_data.summary
        
        # Eski ilişkileri sil
        db.query(Skill).filter(Skill.resume_id == resume_id).delete()
        db.query(Language).filter(Language.resume_id == resume_id).delete()
        db.query(Experience).filter(Experience.resume_id == resume_id).delete()
        db.query(Education).filter(Education.resume_id == resume_id).delete()
        
        # Yeni yetenekleri ekle
        for skill_name in resume_data.skills:
            skill = Skill(resume_id=resume.id, name=skill_name)
            db.add(skill)
        
        # Yeni dilleri ekle
        for lang_name in resume_data.languages:
            language = Language(resume_id=resume.id, name=lang_name)
            db.add(language)
        
        # Yeni deneyimleri ekle
        for exp_data in resume_data.experiences:
            if isinstance(exp_data, dict):
                experience = Experience(
                    resume_id=resume.id,
                    company=exp_data.get('company', ''),
                    position=exp_data.get('position', ''),
                    start_date=exp_data.get('start_date', ''),
                    end_date=exp_data.get('end_date', ''),
                    description=exp_data.get('description', '')
                )
            else:
                experience = Experience(
                    resume_id=resume.id,
                    company=exp_data.company if hasattr(exp_data, 'company') else '',
                    position=exp_data.position if hasattr(exp_data, 'position') else '',
                    start_date=exp_data.start_date if hasattr(exp_data, 'start_date') else '',
                    end_date=exp_data.end_date if hasattr(exp_data, 'end_date') else '',
                    description=exp_data.description if hasattr(exp_data, 'description') else ''
                )
            db.add(experience)
        
        # Yeni eğitimleri ekle
        for edu_data in resume_data.educations:
            if isinstance(edu_data, dict):
                education = Education(
                    resume_id=resume.id,
                    institution=edu_data.get('institution', ''),
                    degree=edu_data.get('degree', ''),
                    field=edu_data.get('field', ''),
                    start_date=edu_data.get('start_date', ''),
                    end_date=edu_data.get('end_date', '')
                )
            else:
                education = Education(
                    resume_id=resume.id,
                    institution=edu_data.institution if hasattr(edu_data, 'institution') else '',
                    degree=edu_data.degree if hasattr(edu_data, 'degree') else '',
                    field=edu_data.field if hasattr(edu_data, 'field') else '',
                    start_date=edu_data.start_date if hasattr(edu_data, 'start_date') else '',
                    end_date=edu_data.end_date if hasattr(edu_data, 'end_date') else ''
                )
            db.add(education)
        
        db.commit()
        
        return {
            "message": "CV başarıyla güncellendi",
            "resume_id": resume.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"CV güncellenemedi: {str(e)}")