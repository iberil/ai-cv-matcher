import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code}
        )
    
    if isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": exc.errors()}
        )
    
    if isinstance(exc, SQLAlchemyError):
        return JSONResponse(
            status_code=500,
            content={"error": "Database error", "status_code": 500}
        )
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )