# 1. Standart Kütüphane
from datetime import timedelta

# 2. Üçüncü Parti Kütüphaneler
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

# 3. Kendi Proje İçi Modüllerin
from ... import models
from ...core import security, config
from ...core.database import get_db
from ...schemas import Token, TokenData, UserCreate, UserRead
from ...services import user_service

router = APIRouter()

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Yeni bir kullanıcı kaydı oluşturur.
    - `user`: Frontend'den gönderilen ve UserCreate şemasına uyan JSON verisi.
    - `db`: get_db dependency'si ile oluşturulan veritabanı oturumu.
    - `response_model`: API'nin başarılı olduğunda UserRead şemasına uygun bir veri döndüreceğini belirtir.
    """
    db_user = user_service.create_user(db=db, user=user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Kullanıcı oluşturulamadı.")
    return db_user

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.settings.access_token_expire_minutes)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# OAuth2 Şeması
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.settings.secret_key, algorithms=[config.settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user