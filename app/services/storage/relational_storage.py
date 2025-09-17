import os
from typing import Any, Dict

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from app.services.storage.base import Storage
from app.models.models import Conversation, Message, Summary  # noqa: F401


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
    """Asynchronous relational storage implementation using SQLModel and PostgreSQL.

    Attributes:
        engine (AsyncEngine): The asynchronous database engine.
        session_local (sessionmaker): The session factory for async sessions.
    """

    def __init__(self) -> None:
        """Initialize the storage with async engine and session factory."""
        self.engine = engine
        self.session_local = AsyncSessionLocal

    async def setup(self) -> None:
        """Create database tables asynchronously based on SQLModel metadata.

        This method initializes the database schema.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def save(self, data: Dict[str, Any]):
        """Save a single vehicle record to the database asynchronously.

        Args:
            data (Dict[str, Any]): The data dictionary representing a vehicle.
        """

        async with self.session_local() as session:
            async with session.begin():
                if "conversation_id" not in data:
                    conversation = Conversation(**data)
                    session.add(conversation)
                    await session.flush()
                    return conversation.id

                else:
                    user_message_data = {
                        "conversation_id": data["conversation_id"],
                        **data["user_message"],
                    }

                    bot_message_data = {
                        "conversation_id": data["conversation_id"],
                        **data["bot_message"],
                    }
                    user_message = Message(**user_message_data)
                    bot_message = Message(**bot_message_data)

                    session.add(user_message)
                    session.add(bot_message)

                    await session.flush()

    async def get(self, filters: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Query vehicle records asynchronously using filter criteria.

        Args:
            filters (Dict[str, Any]): A dictionary of filter conditions.

        Returns:
            List[Dict[str, Any]]: A list of vehicles matching the filters.
        """
        pass

    async def bulk_load(self, data: Dict) -> list[Dict[str, Any]]:
        """Bulk load multiple vehicle records into the database asynchronously.

        Args:
            data (Dict): A dictionary containing a 'records' key with a list of vehicle data.

        Returns:
            List[Dict[str, Any]]: The list of loaded vehicle records.
        """
        pass
