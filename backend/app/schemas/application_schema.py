from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicationRead(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: str
    cover_letter: Optional[str] = None
    applied_at: datetime
    
    class Config:
        from_attributes = True

class ApplicationWithCandidate(BaseModel):
    id: int
    job_id: int
    status: str
    cover_letter: Optional[str] = None
    applied_at: datetime
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    candidate_profession: Optional[str] = None
    
class ApplicationStatusUpdate(BaseModel):
    status: str  # pending, reviewed, accepted, rejected
