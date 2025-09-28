import os
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from app.services.storage.base import Storage
from app.models.models import Conversation, Message  # noqa: F401


DATABASE_URL = os.getenv(
    "DB_ASYNC_CONNECTION_STR",
    "postgresql+asyncpg://carax:carax123@postgres:5432/conversations",
)

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class RelationalStorage(Storage):
    """Async relational storage built on SQLModel + PostgreSQL.

    Attributes:
        engine: Asynchronous database engine.
        session_local: Session factory for async sessions.
    """

    def __init__(self) -> None:
        """Initialize the storage with async engine and session factory."""
        self.engine = engine
        self.session_local = AsyncSessionLocal

    async def setup(self) -> None:
        """Create database tables asynchronously from SQLModel metadata."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def save(self, data: Dict[str, Any]) -> Optional[str]:
        """Persist a conversation or messages depending on the payload.

        If `conversation_id` is absent, creates a new conversation record and
        returns its ID. Otherwise, appends user and bot messages.

        Args:
            data: Conversation metadata or a turn payload.

        Returns:
            str | None: Conversation ID for new conversations; otherwise None.
        """

        async with self.session_local() as session:
            async with session.begin():
                if "conversation_id" not in data:
                    conversation = Conversation(**data)
                    session.add(conversation)
                    await session.flush()
                    return conversation.id

                else:
                    for message in data["messages"]:
                        message_to_persist = Message(
                            conversation_id=data["conversation_id"],
                            role=message.role,
                            content=message.content,
                        )
                        session.add(message_to_persist)

                    await session.flush()

    async def get(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query records using filter criteria.

        Args:
            filters: Dictionary of filter conditions (e.g., table or ids).

        Returns:
            list[Dict[str, Any]]: Records matching the filters.
        """
        pass

    async def bulk_load(self, data: Dict) -> List[Dict[str, Any]]:
        """Bulk insert multiple records asynchronously.

        Args:
            data: Container with records to insert.

        Returns:
            list[Dict[str, Any]]: Inserted records or identifiers.
        """
        pass
