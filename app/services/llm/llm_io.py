from typing import List, Literal

from pydantic import BaseModel

Role = Literal["user", "assistant", "system"]


class LLMConversationMessage(BaseModel):
    role: Role
    content: str


class LLMConversationRequest(BaseModel):
    messages: List[LLMConversationMessage]
