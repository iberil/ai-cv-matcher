from pydantic import BaseModel, EmailStr
from typing import Optional 
from datetime import date 

# --- Kullanıcı Oluşturma Şeması --
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    user_role: str = "aday"
    date_of_birth: Optional[date] = None
    profession: Optional[str] = None

# --- Kullanıcı Okuma Şeması---
class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    user_role: str
    date_of_birth: Optional[date] = None
    profession: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    company_sector: Optional[str] = None
    company_location: Optional[str] = None

    class Config:
        from_attributes = True

# ---  Kullanıcı Güncelleme Şeması ---
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    profession: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    company_sector: Optional[str] = None
    company_location: Optional[str] = None