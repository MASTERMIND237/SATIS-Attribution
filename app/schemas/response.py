from typing import Any, Optional
from pydantic import BaseModel


class ResponseModel(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None
