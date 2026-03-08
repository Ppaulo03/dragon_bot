import asyncio
from sqlalchemy import select, text
from app.modules.finances.database import client, Base
from app.modules.finances.database.models import Category

async def check():
    await client.setup_database(Base.metadata)
    async with client.session_factory() as sess:
        # Check raw count of all categories
        res = await sess.execute(text("SELECT count(*) FROM categories"))
        total = res.scalar()
        
        # Check count of categories where is_deleted is False
        res = await sess.execute(text("SELECT count(*) FROM categories WHERE is_deleted = false"))
        deleted_false = res.scalar()
        
        # Check count where is_deleted is NULL
        res = await sess.execute(text("SELECT count(*) FROM categories WHERE is_deleted IS NULL"))
        is_null = res.scalar()
        
        print(f"Total: {total}, Deleted=False: {deleted_false}, Deleted IS NULL: {is_null}")
        
    await client.close()

if __name__ == "__main__":
    asyncio.run(check())
