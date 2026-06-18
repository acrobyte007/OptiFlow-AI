import asyncio
from sqlalchemy import text
from database.database import db_manager

async def fix_userrole_enum():
    """Add 'CUSTOMER' to userrole enum if it doesn't exist"""
    await db_manager.initialize()
    
    async with db_manager.connect() as session:
        # Check if 'CUSTOMER' exists in the enum
        check_query = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumtypid = 'userrole'::regtype 
                AND enumlabel = 'CUSTOMER'
            )
        """)
        
        result = await session.execute(check_query)
        exists = result.scalar()
        
        if not exists:
            # Add 'CUSTOMER' to the enum
            await session.execute(text("ALTER TYPE userrole ADD VALUE 'CUSTOMER'"))
            await session.commit()
            print("✅ Added 'CUSTOMER' to userrole enum")
        else:
            print("✅ 'CUSTOMER' already exists in userrole enum")

if __name__ == "__main__":
    asyncio.run(fix_userrole_enum())