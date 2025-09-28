import asyncio

from app.services.storage.relational_storage import RelationalStorage


async def setup_all() -> None:
    """Initialize storage backends required by the service.

    Currently sets up the relational database schema.
    """
    print("Initializing PostgreSQL...")
    relational_storage = RelationalStorage()
    await asyncio.gather(relational_storage.setup())


if __name__ == "__main__":
    """Run the async setup when executed as a script."""
    asyncio.run(setup_all())
