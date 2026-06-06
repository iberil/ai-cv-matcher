from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class JobPostingCreate(BaseModel):
    title: str
    company_name: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: Optional[str] = None  # Virgülle ayrılmış
    location: Optional[str] = None
    work_type: Optional[str] = None  # remote, hybrid, office
    job_type: Optional[str] = None  # full-time, part-time, contract
    experience_level: Optional[str] = None  # entry, mid, senior
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    sector: Optional[str] = None

class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: Optional[str] = None
    location: Optional[str] = None
    work_type: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    sector: Optional[str] = None

class JobPostingRead(BaseModel):
    id: int
    title: str
    company_name: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: Optional[str] = None
    location: Optional[str] = None
    work_type: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    sector: Optional[str] = None
    is_active: bool
    created_at: datetime
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True

class JobPostingWithScore(JobPostingRead):
    match_score: float

class JobMatchRequest(BaseModel):
    limit: Optional[int] = 10

class JobMatchResponse(BaseModel):
    matches: List[JobPostingWithScore]
    total_jobs: int
    processing_time: float