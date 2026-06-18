import asyncio
import sys

from database.model import Base
from database.database import db_manager


# Fix for Windows event loop issues
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def reset_database():
    await db_manager.initialize()

    async with db_manager.engine.begin() as conn:
        # 1. Drop all existing tables
        await conn.run_sync(Base.metadata.drop_all)

        # 2. Recreate all tables from current models
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset: all tables dropped and recreated successfully!")


if __name__ == "__main__":
    asyncio.run(reset_database())