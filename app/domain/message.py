from pydantic import BaseModel, computed_field
from typing import Literal, Optional
from datetime import datetime

Role = Literal["user", "assistant", "system"]


class MessageModel(BaseModel):
    id: Optional[int] = None
    role: Role
    content: str
    created_at: Optional[
        datetime
    ]  # TODO Agregar un default con la fecha actual (solo si la base de datos no lo hace primero)

    @computed_field
    @property
    def compact_version(self) -> str:
        return f"{'u' if self.role=='user' else 'a' if self.role =='assistant' else 's'}:{self.content}"
