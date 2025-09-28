from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    code: int
    message: str
    details: Optional[dict] = None
