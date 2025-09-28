from pydantic import BaseModel


class AssistantReply(BaseModel):
    text: str
