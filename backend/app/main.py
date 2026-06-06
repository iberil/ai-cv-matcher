from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .core.exceptions import global_exception_handler
from .models import User
from .models.cv_profile import Resume, Experience, Education, Skill, Language
from .models.job_posting import JobPosting, CVJobMatch
from .models.notification import Notification
from .api.endpoints import auth, users, cv_router, jobs, matching, applications, employer_candidates, notifications, messages, ats_router
import logging

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CV-Matcher API",
    version="1.0.0",
    description="CV ve İş İlanı Eşleştirme Sistemi",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# CORS ayarları - Production
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ai-cv-matcher.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları dahil et
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(cv_router.router, prefix="/api/v1/cv", tags=["CV Management"])
app.include_router(ats_router.router, prefix="/api/v1/cv", tags=["ATS Analysis"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(matching.router, prefix="/api/v1", tags=["Matching"])
app.include_router(applications.router, prefix="/api/v1", tags=["Applications"])
app.include_router(employer_candidates.router, prefix="/api/v1/employer", tags=["Employer Candidates"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {
        "message": "CV-Matcher API başarıyla çalışıyor!",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}