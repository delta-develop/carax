from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, computed_field

Role = Literal["user", "assistant", "system"]


class MessageModel(BaseModel):
    id: Optional[int] = None
    role: Role
    content: str
    created_at: Optional[
        datetime
    ]  # TODO Agregar un default con la fecha actual (solo si la base de datos no lo hace primero)

    @computed_field(return_type=str)
    def compact_version(self) -> str:
        role_initial = 'u' if self.role == 'user' else 'a' if self.role == 'assistant' else 's'
        return f"{role_initial}:{self.content}"
