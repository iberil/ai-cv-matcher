import re
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.cv_profile import Resume, Experience, Education, Skill, Language
from ..schemas import ResumeExtractResponse
from .pdf_service import pdf_to_text, save_temp_file, cleanup_file
from .hf_service import call_qwen_hf
from .regex_service import (
    extract_summary_with_regex, extract_experiences_with_regex,
    extract_educations_with_regex, extract_basic_info_with_regex,
    extract_skills_with_ner, extract_skills_section
)
from .ats_compliance_service import analyze_cv_ats_compliance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# TEMİZLİK VE SANITIZATION
# ─────────────────────────────────────────────────────────────────────────────

def _sanitize_text(text: str) -> str:
    """Metindeki yapısal sızıntıları (SUMMARY, EXPERIENCE gibi başlıklar) temizler."""
    if not text:
        return ""
    
    # Yaygın sızan başlık kelimeleri (Büyük harf ve kelime sonu/başı sınırı ile)
    headers_to_strip = [
        r'\bSUMMARY\b', r'\bWORK\s+EXPERIENCE\b', r'\bEXPERIENCES\b', 
        r'\bEDUCATION\b', r'\bSKILLS\b', r'\bPROJECTS\b', r'\bLANGUAGES\b',
        r'\bADDITIONAL\s+INFORMATION\b', r'\bOBJECTIVE\b', r'\bPROFILE\b'
    ]
    
    clean_text = text
    for pattern in headers_to_strip:
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
    
    # Gereksiz karakterleri ve fazla boşlukları temizle
    clean_text = re.sub(r'[|:;,\-_]{2,}', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK KATMANLARI
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_full_name(cv_text: str) -> str | None:
    """CV'nin ilk satırlarından isim heuristic'i."""
    lines = cv_text.split('\n')
    for line in lines[:6]:
        line = line.strip()
        if (5 < len(line) < 60
                and ' ' in line
                and '@' not in line
                and not re.search(r'\d{4}', line)
                and not any(kw in line.lower() for kw in
                            ['resume', 'cv', 'curriculum', 'vitae', 'profile'])):
            return line
    return None


def _fallback_languages(cv_text: str) -> list:
    """Regex ile dil isimlerini ve seviyelerini tespit eder."""
    lang_pattern = (
        r'\b(ingilizce|almanca|fransizca|ispanyolca|rusca|arapca|italyanca|'
        r'cince|japonca|turkce|korece|portekizce|hollandaca|'
        r'english|german|french|spanish|russian|arabic|'
        r'italian|chinese|japanese|turkish|korean|portuguese|dutch)\b'
        r'(?:[\s:\-\(]*'
        r'([A-C][1-2]|Native|Anadil|Fluent|Akici|Advanced|'
        r'Intermediate|Orta|Basic|Baslangic|Elementary)'
        r'(?:\))?)?'
    )
    found: list = []
    seen_langs: dict = {} # {base_name: full_string}
    
    for m in re.findall(lang_pattern, cv_text, re.IGNORECASE):
        lang_base = m[0].capitalize()
        level = m[1]
        full_lang = f"{lang_base} ({level})" if level else lang_base
        
        # Daha detaylı (seviyeli) olanı tercih et
        if lang_base not in seen_langs or '(' in full_lang:
            seen_langs[lang_base] = full_lang
            
    found = list(seen_langs.values())
    return found


def _enrich_skills(result: dict, cv_text: str) -> None:
    """
    LLM'nin bulduğu becerileri Regex + NER ile zenginleştirir.
    Sadece eksik / az sayıda beceri varsa devreye girer.
    """
    existing_lower = {s.lower() for s in result.get('skills', [])}

    # Önce Skills bölümünden regex ile çek
    section_skills = extract_skills_section(cv_text)
    for s in section_skills:
        if s.lower() not in existing_lower:
            result['skills'].append(s)
            existing_lower.add(s.lower())

    # Hâlâ yetersizse BERT-NER + keyword matching devreye girer
    if len(result['skills']) < 8:
        ner_result = extract_skills_with_ner(cv_text)
        for s in ner_result['skills']:
            if s.lower() not in existing_lower:
                result['skills'].append(s)
                existing_lower.add(s.lower())


def _apply_field_fallbacks(result: dict, cv_text: str, source: str = "qwen") -> dict:
    """
    LLM sonucunda eksik/yetersiz alanlar için bölümsel fallback uygular.
    Her fallback devreye girdiğinde log kaydı atar.
    """

    # ── full_name ────────────────────────────────────────────────────────────
    if result.get('full_name'):
        # Mevcut ismi temizle (sızıntı varsa)
        result['full_name'] = _sanitize_text(result['full_name'])
        
    if not result.get('full_name') or len(result.get('full_name', '')) < 3:
        name = _fallback_full_name(cv_text)
        if name:
            logger.warning(f"[{source}] full_name eksik → heuristic devreye girdi: '{name}'")
            result['full_name'] = _sanitize_text(name)

    # ── email / phone ────────────────────────────────────────────────────────
    if not result.get('email') or not result.get('phone'):
        basic = extract_basic_info_with_regex(cv_text)
        if not result.get('email') and basic.get('email'):
            logger.warning(f"[{source}] email eksik → regex devreye girdi.")
            result['email'] = basic['email']
        if not result.get('phone') and basic.get('phone'):
            logger.warning(f"[{source}] phone eksik → regex devreye girdi.")
            result['phone'] = basic['phone']

    # ── summary ─────────────────────────────────────────────────────────────
    if not result.get('summary') or len(result.get('summary', '')) < 30:
        summary = extract_summary_with_regex(cv_text)
        if not summary:
            exps = result.get('experiences', [])
            skls = result.get('skills', [])
            
            # Daha profesyonel bir fallback üret
            prof_title = ""
            if exps:
                prof_title = exps[0].get('position', '')
            
            if prof_title:
                summary = f"{prof_title} alanında {len(exps)} deneyim ve {len(skls)} beceriye sahip nitelikli profesyonel."
            else:
                summary = f"{len(exps)} iş deneyimi ve {len(skls)} teknik beceri ile profesyonel profil."
                
        logger.warning(f"[{source}] summary eksik/kısa → regex devreye girdi.")
        result['summary'] = summary

    # ── experiences ──────────────────────────────────────────────────────────
    if not result.get('experiences'):
        logger.warning(f"[{source}] experiences boş → regex devreye girdi.")
        result['experiences'] = extract_experiences_with_regex(cv_text)

    # ── educations ───────────────────────────────────────────────────────────
    if not result.get('educations'):
        logger.warning(f"[{source}] educations boş → regex devreye girdi.")
        result['educations'] = extract_educations_with_regex(cv_text)

    # ── skills ───────────────────────────────────────────────────────────────
    result.setdefault('skills', [])
    if len(result['skills']) < 5:
        logger.warning(
            f"[{source}] skills yetersiz ({len(result['skills'])} adet) → "
            f"Regex + NER devreye girdi."
        )
        _enrich_skills(result, cv_text)
    else:
        # Yeterli sayıda var ama yine de section-regex ile tamamla
        existing_lower = {s.lower() for s in result['skills']}
        for s in extract_skills_section(cv_text):
            if s.lower() not in existing_lower:
                result['skills'].append(s)
                existing_lower.add(s.lower())

    # ── languages ────────────────────────────────────────────────────────────
    if not result.get('languages'):
        langs = _fallback_languages(cv_text)
        if langs:
            logger.warning(f"[{source}] languages boş → regex devreye girdi.")
            result['languages'] = langs

    return result


def _full_regex_fallback(cv_text: str) -> dict:
    """
    LLM tamamen başarısız olduğunda devreye giren tam Regex/NER yedek sistemi.
    """
    logger.error("LLM başarısız → Tam Regex/NER fallback aktif.")

    basic_info = extract_basic_info_with_regex(cv_text)
    experiences = extract_experiences_with_regex(cv_text)
    educations = extract_educations_with_regex(cv_text)

    # Beceri: bölüm regex + NER
    section_skills = extract_skills_section(cv_text)
    ner_skills = extract_skills_with_ner(cv_text)['skills']
    seen: set = set()
    skills: list = []
    for s in section_skills + ner_skills:
        if s.lower() not in seen:
            seen.add(s.lower())
            skills.append(s)

    full_name = _fallback_full_name(cv_text)
    summary = extract_summary_with_regex(cv_text)
    if not summary:
        lines = cv_text.split('\n')
        title_line = ""
        for line in lines[:10]:
            line = line.strip()
            if (10 < len(line) < 80
                    and '@' not in line
                    and not any(c.isdigit() for c in line[:3])):
                if line != full_name:
                    title_line = line
                    break
        summary = (
            f"{title_line} alanında {len(experiences)} deneyim ve {len(skills)} "
            f"beceri ile profesyonel profil."
            if title_line
            else f"{len(experiences)} iş deneyimi ve {len(skills)} beceri ile profesyonel profil."
        )

    result = {
        "full_name": full_name,
        "email": basic_info.get('email'),
        "phone": basic_info.get('phone'),
        "summary": summary,
        "skills": skills,
        "languages": _fallback_languages(cv_text),
        "experiences": experiences,
        "educations": educations,
        "_extraction_method": "regex_ner_fallback",
    }

    logger.info("--- DEBUG: TAM SONUÇ (Regex/NER Fallback) ---")
    logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ANA FONKSİYON
# ─────────────────────────────────────────────────────────────────────────────

def extract_features(file_path: str) -> dict:
    """
    Hibrit yaklaşımla CV'den yapısal veri çıkarır.

    Birincil:   Qwen/Qwen2.5-72B-Instruct (Hugging Face Inference API)
                → Yüksek doğruluklu anlamsal analiz, JSON formatında çıktı

    İkincil:    Bölümsel Regex + dslim/bert-base-NER fallback
                → LLM'nin gözden kaçırdığı alanları tamamlar

    Tam Yedek:  Tüm LLM denemesi başarısız olursa saf Regex/NER sistemi
    
    ATS Analizi: CV çıkarıldıktan sonra otomatik ATS uyumluluk analizi yapılır
    """
    cv_text = pdf_to_text(file_path)
    if not cv_text or not cv_text.strip():
        logger.error("PDF'den metin çıkarılamadı.")
        return {}

    logger.info(f"CV metni çıkarıldı ({len(cv_text)} karakter). İlk 300: {cv_text[:300]}...")

    # ── 1. BİRİNCİL: Qwen2.5-72B via HF Inference API ───────────────────────
    result = call_qwen_hf(cv_text)

    if not result:
        # ── 2. TAM YEDEK: Regex + NER ────────────────────────────────────────
        result = _full_regex_fallback(cv_text)
    else:
        # ── 3. BÖLÜMSEL FALLBACK: Eksik alanları tamamla ─────────────────────────
        result.setdefault('skills', [])
        result.setdefault('languages', [])
        result.setdefault('experiences', [])
        result.setdefault('educations', [])
        result['_extraction_method'] = 'qwen2.5_hf'

        result = _apply_field_fallbacks(result, cv_text, source="qwen2.5")

    logger.info("--- DEBUG: TAM SONUÇ (Qwen2.5 + Bölümsel Fallback) ---")
    logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    
    # ── 4. ATS UYUMLULUK ANALİZİ ─────────────────────────────────────────────
    try:
        logger.info("ATS uyumluluk analizi başlatılıyor...")
        ats_report = analyze_cv_ats_compliance(cv_text, file_path, result)
        result['_ats_report'] = ats_report
        logger.info(f"ATS analizi tamamlandı. Skor: {ats_report.get('overall_score', 0)}/100")
    except Exception as e:
        logger.error(f"ATS analizi başarısız: {e}")
        result['_ats_report'] = None
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# VERİTABANI İŞLEMLERİ
# ─────────────────────────────────────────────────────────────────────────────

def save_resume_to_db(
    db: Session,
    user_id: int,
    resume_data: ResumeExtractResponse,
    file_path: str = None,
) -> Resume:
    """
    Kullanıcı onayladıktan sonra CV'yi veritabanına kaydeder veya GÜNCELLER.
    Çifte kayıt önleme sistemi ile.
    """

    # 1. Aynı kullanıcının aynı isimle kayıtlı CV'si var mı?
    existing_resume = db.query(Resume).filter(
        Resume.user_id == user_id,
        Resume.full_name == resume_data.full_name
    ).first()

    if existing_resume:
        logger.info(f"--- DEBUG: Mevcut CV güncelleniyor: ID {existing_resume.id} ---")

        existing_resume.email = resume_data.email
        existing_resume.phone = resume_data.phone
        existing_resume.summary = resume_data.summary
        if file_path:
            existing_resume.file_path = file_path

        db.query(Experience).filter(Experience.resume_id == existing_resume.id).delete()
        db.query(Education).filter(Education.resume_id == existing_resume.id).delete()
        db.query(Skill).filter(Skill.resume_id == existing_resume.id).delete()
        db.query(Language).filter(Language.resume_id == existing_resume.id).delete()

        resume = existing_resume
    else:
        from datetime import datetime, timedelta
        recent_threshold = datetime.utcnow() - timedelta(minutes=5)

        recent_resume = db.query(Resume).filter(
            Resume.user_id == user_id,
            Resume.created_at >= recent_threshold
        ).first()

        if recent_resume:
            logger.warning(f"--- UYARI: Çifte kayıt engellendi: ID {recent_resume.id} ---")
            return recent_resume

        logger.info("--- DEBUG: Yeni CV oluşturuluyor ---")
        resume = Resume(
            user_id=user_id,
            full_name=resume_data.full_name,
            email=resume_data.email,
            phone=resume_data.phone,
            summary=resume_data.summary,
            file_path=file_path
        )
        db.add(resume)
        db.flush()

    for exp in resume_data.experiences:
        db.add(Experience(
            resume_id=resume.id,
            company=exp.company,
            position=exp.position,
            start_date=exp.start_date,
            end_date=exp.end_date,
            description=exp.description
        ))

    for edu in resume_data.educations:
        db.add(Education(
            resume_id=resume.id,
            institution=edu.institution,
            degree=edu.degree,
            field=edu.field,
            start_date=edu.start_date,
            end_date=edu.end_date
        ))

    for skill_name in resume_data.skills:
        db.add(Skill(resume_id=resume.id, name=skill_name))

    for lang in resume_data.languages:
        db.add(Language(resume_id=resume.id, name=lang))

    db.commit()
    db.refresh(resume)
    return resume


def delete_user_cv(db: Session, resume_id: int, user_id: int) -> bool:
    """
    Belirtilen CV'yi ve ilişkili tüm verileri siler.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        return False

    if resume.file_path:
        cleanup_file(resume.file_path)

    db.delete(resume)
    db.commit()

    logger.info(f"CV DB'den silindi: ID {resume_id}")
    return True