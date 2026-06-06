from pydantic import BaseModel
from typing import List, Optional

class SalaryAnalysis(BaseModel):
    your_min: Optional[int]
    your_max: Optional[int]
    market_avg_min: float
    market_avg_max: float
    competitiveness: str  # "below", "average", "above"
    message: str

class SkillAnalysis(BaseModel):
    your_skills: List[str]
    trending_skills: List[str]
    missing_skills: List[str]
    match_percentage: float

class WorkTypeAnalysis(BaseModel):
    your_work_type: str
    market_distribution: dict  # {"remote": 30, "hybrid": 50, "office": 20}
    message: str

class CompetitorAnalysisResponse(BaseModel):
    job_id: int
    job_title: str
    total_similar_jobs: int
    salary_analysis: SalaryAnalysis
    skill_analysis: SkillAnalysis
    work_type_analysis: WorkTypeAnalysis
