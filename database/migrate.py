import asyncio
from database.database import db_manager
from database.model import Base

async def migrate():
    """Create all tables including new ones"""
    await db_manager.initialize()
    
    async with db_manager.engine.begin() as conn:
        # This will create all tables that don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    print("All tables migrated successfully!")
    await db_manager.close_all()

if __name__ == "__main__":
    asyncio.run(migrate())