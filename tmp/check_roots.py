import asyncio
from sqlalchemy import select
from app.modules.finances.database import client, Base
from app.modules.finances.database.models import Category

async def check():
    await client.setup_database(Base.metadata)
    async with client.session_factory() as sess:
        # Check all categories with parent_id is None
        res = await sess.execute(select(Category).where(Category.parent_id == None))
        roots = res.scalars().all()
        print("--- Root Categories (parent_id is None) ---")
        for r in roots:
            print(f"ID: {r.id}, Name: {r.name}, Type: {r.transaction_type}, Level: {r.level}")
        
        # Check if 'Saída', 'Entrada' or 'Transferência' exist as names
        res = await sess.execute(select(Category).where(Category.name.in_(['Entrada', 'Saída', 'Transferência'])))
        named_roots = res.scalars().all()
        print("\n--- Categories named Entrada/Saída/Transferência ---")
        for nr in named_roots:
            print(f"ID: {nr.id}, Name: {nr.name}, Type: {nr.transaction_type}, Level: {nr.level}, Parent: {nr.parent_id}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(check())
