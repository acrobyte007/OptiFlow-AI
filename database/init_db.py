import asyncio
from database.model import Base
from database.database import db_manager


async def create_tables():
    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())