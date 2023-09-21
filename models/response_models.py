from pydantic import BaseModel

class ErrorResponse(BaseModel):
    success: bool
    unsuccess_reason: str

from fastapi import HTTPException

class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: ErrorResponse):
        super().__init__(status_code=status_code, detail=detail.dict())