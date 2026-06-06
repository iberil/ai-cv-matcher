from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.job_posting import JobPosting
from ..schemas.analysis_schema import (
    CompetitorAnalysisResponse,
    SalaryAnalysis,
    SkillAnalysis,
    WorkTypeAnalysis
)
from typing import List

def _get_similar_jobs(job: JobPosting, db: Session) -> List[JobPosting]:
    """Benzer iş ilanlarını getir (aynı title ve experience_level)"""
    similar_jobs = db.query(JobPosting).filter(
        JobPosting.id != job.id,
        JobPosting.is_active == True,
        JobPosting.title.ilike(f"%{job.title}%"),
        JobPosting.experience_level == job.experience_level
    ).all()
    return similar_jobs

def analyze_salary(job: JobPosting, similar_jobs: List[JobPosting]) -> SalaryAnalysis:
    """Maaş analizi yap"""
    if not similar_jobs:
        return SalaryAnalysis(
            your_min=job.salary_min,
            your_max=job.salary_max,
            market_avg_min=0,
            market_avg_max=0,
            competitiveness="unknown",
            message="Karşılaştırma için yeterli veri yok"
        )
    
    valid_salaries = [(j.salary_min, j.salary_max) for j in similar_jobs if j.salary_min and j.salary_max]
    
    if not valid_salaries:
        return SalaryAnalysis(
            your_min=job.salary_min,
            your_max=job.salary_max,
            market_avg_min=0,
            market_avg_max=0,
            competitiveness="unknown",
            message="Piyasada maaş bilgisi bulunamadı"
        )
    
    market_avg_min = sum(s[0] for s in valid_salaries) / len(valid_salaries)
    market_avg_max = sum(s[1] for s in valid_salaries) / len(valid_salaries)
    
    your_avg = ((job.salary_min or 0) + (job.salary_max or 0)) / 2 if job.salary_min and job.salary_max else 0
    market_avg = (market_avg_min + market_avg_max) / 2
    
    if your_avg == 0:
        competitiveness = "unknown"
        message = "İlanınızda maaş bilgisi belirtilmemiş"
    elif your_avg < market_avg * 0.9:
        competitiveness = "below"
        message = "Maaş aralığınız piyasa ortalamasının altında"
    elif your_avg > market_avg * 1.1:
        competitiveness = "above"
        message = "Maaş aralığınız piyasa ortalamasının üstünde - Rekabetçi!"
    else:
        competitiveness = "average"
        message = "Maaş aralığınız piyasa ortalamasında"
    
    return SalaryAnalysis(
        your_min=job.salary_min,
        your_max=job.salary_max,
        market_avg_min=round(market_avg_min, 2),
        market_avg_max=round(market_avg_max, 2),
        competitiveness=competitiveness,
        message=message
    )

def analyze_skills(job: JobPosting, similar_jobs: List[JobPosting]) -> SkillAnalysis:
    """Beceri analizi yap"""
    your_skills = [s.strip().lower() for s in (job.skills_required or "").split(",") if s.strip()]
    
    if not similar_jobs:
        return SkillAnalysis(
            your_skills=your_skills,
            trending_skills=[],
            missing_skills=[],
            match_percentage=0
        )
    
    # Piyasadaki tüm becerileri topla ve frekanslarını hesapla
    skill_freq = {}
    for j in similar_jobs:
        skills = [s.strip().lower() for s in (j.skills_required or "").split(",") if s.strip()]
        for skill in skills:
            skill_freq[skill] = skill_freq.get(skill, 0) + 1
    
    # En popüler 10 beceriyi al
    trending_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    trending_skills = [s[0] for s in trending_skills]
    
    # Eksik becerileri bul
    missing_skills = [s for s in trending_skills if s not in your_skills]
    
    # Eşleşme yüzdesi
    match_percentage = (len([s for s in your_skills if s in trending_skills]) / len(trending_skills) * 100) if trending_skills else 0
    
    return SkillAnalysis(
        your_skills=your_skills,
        trending_skills=trending_skills,
        missing_skills=missing_skills,
        match_percentage=round(match_percentage, 2)
    )

def analyze_work_type(job: JobPosting, similar_jobs: List[JobPosting]) -> WorkTypeAnalysis:
    """Çalışma tipi analizi yap"""
    if not similar_jobs:
        return WorkTypeAnalysis(
            your_work_type=job.work_type or "unknown",
            market_distribution={},
            message="Karşılaştırma için yeterli veri yok"
        )
    
    # Çalışma tipi dağılımını hesapla
    work_type_count = {}
    for j in similar_jobs:
        wt = j.work_type or "unknown"
        work_type_count[wt] = work_type_count.get(wt, 0) + 1
    
    total = len(similar_jobs)
    market_distribution = {k: round((v / total) * 100, 2) for k, v in work_type_count.items()}
    
    your_wt = job.work_type or "unknown"
    your_percentage = market_distribution.get(your_wt, 0)
    
    if your_percentage > 40:
        message = f"Çalışma tipiniz ({your_wt}) piyasada çok yaygın (%{your_percentage})"
    elif your_percentage > 20:
        message = f"Çalışma tipiniz ({your_wt}) piyasada orta düzeyde yaygın (%{your_percentage})"
    else:
        message = f"Çalışma tipiniz ({your_wt}) piyasada az tercih ediliyor (%{your_percentage})"
    
    return WorkTypeAnalysis(
        your_work_type=your_wt,
        market_distribution=market_distribution,
        message=message
    )

def generate_competitor_analysis(job_id: int, db: Session) -> CompetitorAnalysisResponse:
    """Ana analiz fonksiyonu"""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise ValueError("İlan bulunamadı")
    
    similar_jobs = _get_similar_jobs(job, db)
    
    salary_analysis = analyze_salary(job, similar_jobs)
    skill_analysis = analyze_skills(job, similar_jobs)
    work_type_analysis = analyze_work_type(job, similar_jobs)
    
    return CompetitorAnalysisResponse(
        job_id=job.id,
        job_title=job.title,
        total_similar_jobs=len(similar_jobs),
        salary_analysis=salary_analysis,
        skill_analysis=skill_analysis,
        work_type_analysis=work_type_analysis
    )
