# 1. Üçüncü Parti Kütüphaneler
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 2. Kendi Proje İçi Modüllerin
from ... import models
from ...core.database import get_db
from ...schemas import UserRead, UserUpdate 
from ...services import user_service 
from . import auth

router = APIRouter()


@router.get("/me", response_model=UserRead) 
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserRead) 
def update_user_me(
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return user_service.update_user(db=db, user=current_user, user_update=user_update) 