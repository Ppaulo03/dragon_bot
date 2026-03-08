import asyncio
from sqlalchemy import select
from app.modules.finances.database import client, Base
from app.modules.finances.database.models import Category

async def check():
    await client.setup_database(Base.metadata)
    async with client.session_factory() as sess:
        res = await sess.execute(select(Category.transaction_type).distinct())
        types = res.scalars().all()
        print(f"Types: {types}")
        
        res = await sess.execute(select(Category).limit(5))
        cats = res.scalars().all()
        for c in cats:
            print(f"Cat: {c.name}, Type: {c.transaction_type}, Level: {c.level}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(check())
