from typing import Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: int
    message: str
    details: Optional[dict] = None
