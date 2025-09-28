from pydantic import BaseModel
from typing import Literal, List

Role = Literal["user", "assistant", "system"]


class LLMConversationMessage(BaseModel):
    role: Role
    content: str


class LLMConversationRequest(BaseModel):
    messages: List[LLMConversationMessage]
