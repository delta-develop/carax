from pydantic import BaseModel, Field


class AssistantReply(BaseModel):
    text: str
