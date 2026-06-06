from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...api.endpoints.auth import get_current_user
from ...models.user import User
from ...models.cv_profile import Resume
from ...schemas.ats_schema import ATSScoreResponse, ATSAnalysisRequest, CareerChatRequest
from ...services.ats_service import ats_service
from ...services.pdf_service import pdf_to_text
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{cv_id}/analyze-ats", response_model=ATSScoreResponse)
async def analyze_cv_ats(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Belirli bir CV'yi ATS gözüyle analiz eder ve skor döner.
    """
    # CV'yi bul
    resume = db.query(Resume).filter(
        Resume.id == cv_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="CV bulunamadı")
    
    try:
        if resume.file_path:
            try:
                # Metni PDF'den çıkar
                cv_text = pdf_to_text(resume.file_path)
            except Exception:
                cv_text = ""
        else:
            cv_text = ""

        # Eğer PDF'den metin alamadıysak DB'deki mevcut verilerle metin oluşturalım
        if not cv_text or len(cv_text.strip()) < 50:
            texts = [resume.full_name or "", resume.summary or ""]
            if resume.skills:
                texts.append("Yetenekler")
                texts.append(" ".join(s.name for s in resume.skills))
            if resume.experiences:
                texts.append("Deneyim")
                for e in resume.experiences:
                    texts.append(e.position or "")
                    texts.append(e.company or "")
                    texts.append(e.description or "")
            if resume.educations:
                texts.append("Eğitim")
                for edu in resume.educations:
                    texts.append(edu.degree or "")
                    texts.append(edu.field or "")
                    texts.append(edu.institution or "")
            cv_text = "\n".join(texts)

        # Analizi gerçekleştir
        analysis_results = ats_service.perform_full_analysis(cv_text, resume.file_path or "")
        
        # Yaratılan datatime alanını string'e çevirerek JSON parse errorlarını önle
        report_data = analysis_results.copy()
        if 'analyzed_at' in report_data and hasattr(report_data['analyzed_at'], 'isoformat'):
            report_data['analyzed_at'] = report_data['analyzed_at'].isoformat()
            
        resume.ats_score = analysis_results['overall_score']
        resume.ats_compliance_level = analysis_results['compliance_level']
        resume.ats_report = report_data
        resume.ats_analyzed_at = analysis_results['analyzed_at']
        
        db.commit()
        
        return ATSScoreResponse(**analysis_results)
        
    except Exception as e:
        logger.error(f"ATS analiz hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ATS analizi sırasında bir hata oluşti: {str(e)}")

@router.get("/{cv_id}/career-advice")
async def get_career_advice(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mevcut ATS analizine göre AI Kariyer Koçu tavsiyesi getirir.
    """
    resume = db.query(Resume).filter(
        Resume.id == cv_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume or not resume.ats_report:
        raise HTTPException(status_code=400, detail="Önce ATS analizi yapmalısınız.")
    
    try:
        if resume.file_path:
            try:
                cv_text = pdf_to_text(resume.file_path)
            except Exception:
                cv_text = ""
        else:
            cv_text = ""
            
        if not cv_text or len(cv_text.strip()) < 50:
            texts = [resume.full_name or "", resume.summary or ""]
            if resume.skills:
                texts.append("Yetenekler")
                texts.append(" ".join(s.name for s in resume.skills))
            if resume.experiences:
                texts.append("Deneyim")
                for e in resume.experiences:
                    texts.append(e.position or "")
                    texts.append(e.company or "")
                    texts.append(e.description or "")
            if resume.educations:
                texts.append("Eğitim")
                for edu in resume.educations:
                    texts.append(edu.degree or "")
                    texts.append(edu.field or "")
            cv_text = "\n".join(texts)
    except Exception:
        cv_text = str(resume.ats_report)

    advice = ats_service.get_ai_career_advice(cv_text, resume.ats_report)
    
    return {"advice": advice}

@router.post("/{cv_id}/career-chat")
async def chat_with_career_coach(
    cv_id: int,
    request: CareerChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kariyer koçu ile interaktif sohbet.
    """
    resume = db.query(Resume).filter(
        Resume.id == cv_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume or not resume.ats_report:
        raise HTTPException(status_code=400, detail="Önce ATS analizi yapmalısınız.")
    
    try:
        if resume.file_path:
            try:
                cv_text = pdf_to_text(resume.file_path)
            except Exception:
                cv_text = ""
        else:
            cv_text = ""
            
        if not cv_text or len(cv_text.strip()) < 50:
            cv_text = str(resume.ats_report)
    except Exception:
        cv_text = str(resume.ats_report)

    message_dicts = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    response_text = ats_service.chat_with_career_coach(cv_text, resume.ats_report, message_dicts)
    
    return {"advice": response_text}
