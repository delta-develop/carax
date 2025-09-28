from typing import Dict, List, Literal

from pydantic import BaseModel

Role = Literal["user", "assistant"]


class Turn(BaseModel):
    role: Role
    message: str


class ConversationResponse(BaseModel):
    conversation_id: str
    message: List[Dict]
