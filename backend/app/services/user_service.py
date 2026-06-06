from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .. import models
from ..schemas import UserCreate
from ..core import security
from fastapi import HTTPException
from .. import schemas
import logging

logger = logging.getLogger(__name__)

def create_user(db: Session, user: schemas.UserCreate):
    try:
        # 1. Aynı e-posta ile başka bir kullanıcı var mı diye kontrol et
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")

        # 2. Gelen düz metin şifreyi hash'le
        hashed_password = security.get_password_hash(user.password)

        # 3. Yeni bir User modeli nesnesi oluştur
        new_user = models.User(
            full_name=user.full_name,
            email=user.email,
            hashed_password=hashed_password,
            user_role=user.user_role,
            date_of_birth=user.date_of_birth,
            profession=user.profession
        )

        # 4. Veritabanına ekle, kaydet ve değişiklikleri yansıt
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User created successfully: {user.email}")
        return new_user
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating user: {e}")
        raise HTTPException(status_code=500, detail="Veritabanı hatası")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(status_code=500, detail="Beklenmeyen hata")


def authenticate_user(db: Session, email: str, password: str):
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return None
        if not security.verify_password(password, user.hashed_password):
            return None
        return user
    except SQLAlchemyError as e:
        logger.error(f"Database error authenticating user: {e}")
        return None


def update_user(db: Session, user: models.User, user_update: schemas.UserUpdate):
    try:
        update_data = user_update.dict(exclude_unset=True)
        
        # Validation: Boş değerler kontrolü
        for key, value in update_data.items():
            if value is not None and str(value).strip():
                setattr(user, key, value)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated successfully: {user.email}")
        return user
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating user: {e}")
        raise HTTPException(status_code=500, detail="Veritabanı hatası")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating user: {e}")
        raise HTTPException(status_code=500, detail="Beklenmeyen hata")