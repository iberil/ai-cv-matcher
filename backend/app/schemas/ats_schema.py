from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class ATSIssue(BaseModel):
    """ATS uyumluluk sorunu"""
    severity: str  # critical, error, warning, info
    message: str
    category: Optional[str] = None


class ATSScoreResponse(BaseModel):
    """ATS Analiz Sonuç Şeması (Yeni)"""
    overall_score: int
    layout_score: int
    content_score: int
    action_verb_count: int
    improvement_suggestions: List[str]
    compliance_level: str
    feedback: List[Dict[str, str]] # { "type": "critical", "message": "..." }
    found_keywords: Optional[List[str]] = None
    analyzed_at: datetime



class ATSAnalysisRequest(BaseModel):
    """ATS analiz isteği"""
    cv_id: int

class ChatMessage(BaseModel):
    role: str
    content: str

class CareerChatRequest(BaseModel):
    messages: List[ChatMessage]
