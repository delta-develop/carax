# app/db/models.py
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Conversation(SQLModel, table=True):  # type: ignore[call-arg]
    """Conversation header storing debate topic and bot stance."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    topic: str
    stance: str
    created_at: datetime = Field(default_factory=datetime.now)

    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):  # type: ignore[call-arg]
    """Single message belonging to a conversation (user or assistant)."""

    id: Optional[int] = Field(default=None, primary_key=True)  # autoincrement
    conversation_id: str = Field(foreign_key="conversation.id")
    role: RoleEnum

    content: Dict[str, Any] = Field(sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.now)

    conversation: "Conversation" = Relationship(back_populates="messages")
