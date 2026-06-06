import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy motorunu oluştur. Bu, veritabanına olan ana bağlantı noktasıdır.
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Veritabanı oturumları (session) oluşturmak için bir fabrika.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modellerimizin (veritabanı tabloları) miras alacağı temel sınıf.
Base = declarative_base()

# Dependency Injection için: Her API isteği için yeni bir veritabanı oturumu açar
# ve işlem bittiğinde (başarılı veya hatalı) oturumu kapatır.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()