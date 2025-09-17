# app/db/models.py
from __future__ import annotations
from typing import Optional, Literal, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid

Role = Literal["user", "assistant", "system"]


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    topic: str
    stance: str
    created_at: datetime = Field(default_factory=datetime.now)

    messages: List["Message"] = Relationship(back_populates="conversation")
    summaries: List["Summary"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)  # autoincrement
    conversation_id: str = Field(foreign_key="conversation.id")
    role: Role

    content: Dict[str, Any] = Field(sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.now)

    conversation: Conversation = Relationship(back_populates="messages")


class Summary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id")
    version: int
    # resumen denso que se inyecta en el prompt
    summary: str
    # control de qué mensajes ya fueron “absorbidos” por el resumen
    first_message_id: int  # inclusive
    last_message_id: int  # inclusive
    tokens_estimate: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

    conversation: Conversation = Relationship(back_populates="summaries")
