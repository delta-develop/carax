from typing import Optional

from pydantic import BaseModel, Field


class ConversationRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=20)
