from pydantic import BaseModel


class MetaModel(BaseModel):
    topic: str
    stance: str
