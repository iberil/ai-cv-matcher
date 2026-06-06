from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone 
from typing import Any
import jwt 
from . import config 

# Şifre hash'leme algoritmasını belirliyoruz. bcrypt en popüler ve güvenli olanlardan biridir.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Verilen bir şifreyi doğrulamak için (giriş yaparken kullanılacak)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Düz metin bir şifreyi hash'lemek için (kayıt olurken kullanılacak)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Eğer süre verilmezse 15 dakika geçerli olsun
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt