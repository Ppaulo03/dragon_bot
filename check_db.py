import asyncio
from sqlalchemy import text
from src.app.modules.finances.database import client

async def check_columns():
    async with client.engine.connect() as conn:
        for table in ['templates', 'accounts', 'transactions', 'categories', 'users']:
            result = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            columns = [row[0] for row in result.fetchall()]
            print(f"Columns in '{table}': {columns}")

if __name__ == "__main__":
    asyncio.run(check_columns())
