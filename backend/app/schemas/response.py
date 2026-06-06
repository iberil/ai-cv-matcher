from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "İşlem başarılı"
    data: Optional[T] = None
    status_code: int = 200

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    status_code: int = 400

def success_response(data: Any = None, message: str = "İşlem başarılı", status_code: int = 200):
    return APIResponse(
        success=True,
        message=message,
        data=data,
        status_code=status_code
    )

def error_response(message: str, error_code: str = None, status_code: int = 400):
    return ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        status_code=status_code
    )