# app/db/models.py
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid


class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Conversation(SQLModel, table=True):
    """Conversation header storing debate topic and bot stance."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    topic: str
    stance: str
    created_at: datetime = Field(default_factory=datetime.now)

    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """Single message belonging to a conversation (user or assistant)."""

    id: Optional[int] = Field(default=None, primary_key=True)  # autoincrement
    conversation_id: str = Field(foreign_key="conversation.id")
    role: RoleEnum

    content: Dict[str, Any] = Field(sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.now)

    conversation: "Conversation" = Relationship(back_populates="messages")
