from pydantic import BaseModel
from typing import Literal, List, Dict

Role = Literal["user", "assistant"]


class Turn(BaseModel):
    role: Role
    message: str


class ConversationResponse(BaseModel):
    conversation_id: str
    message: List[Dict]
