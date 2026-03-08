import asyncio
from sqlalchemy import text
from src.app.modules.finances.database import client

async def fix_schema():
    print("🚀 Starting database schema fix...")
    async with client.engine.begin() as conn:
        # 1. Fix Templates table: Add local_id and index
        print("📝 Patching 'templates' table...")
        await conn.execute(text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS local_id VARCHAR(50);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_templates_local_id ON templates (local_id);"))
        print("✅ 'templates' table patched.")

        # 2. Fix Categories table: Change color_hex type to BIGINT
        print("📝 Patching 'categories' table...")
        await conn.execute(text("ALTER TABLE categories ALTER COLUMN color_hex TYPE BIGINT;"))
        print("✅ 'categories' table patched.")

    print("🎉 Database schema fix completed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_schema())
