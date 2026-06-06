from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    receiver_id: int
    job_id: Optional[int] = None
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    job_id: Optional[int]
    content: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    other_user_id: int
    other_user_name: str
    last_message: str
    last_message_at: Optional[datetime]
    unread_count: int
    
    class Config:
        from_attributes = True
