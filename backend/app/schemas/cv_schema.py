from pydantic import BaseModel
from typing import Optional, List

class ExperienceCreate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class EducationCreate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ResumeExtractResponse(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    languages: List[str] = []
    experiences: List[ExperienceCreate] = []
    educations: List[EducationCreate] = []
    total_experience_years: Optional[float] = 0.0
    file_path: Optional[str] = None

    class Config:
        from_attributes = True