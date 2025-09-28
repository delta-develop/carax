from pydantic import BaseModel, Field
from typing import Optional


class ConversationRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=20)
