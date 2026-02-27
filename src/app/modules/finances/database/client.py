from app.kernel import PostgresClient
from ..configs import settings

client = PostgresClient(
    database_url=settings.database_url, db_name=settings.POSTGRES_DB
)


async def get_db_session():
    async with client.session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
