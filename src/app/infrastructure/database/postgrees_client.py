from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config import settings
from app.infrastructure.database.models import Base
from loguru import logger


class PostgresClient:
    """
    Gerenciador de conexão com o PostgreSQL.
    """

    def __init__(self):
        self.engine = create_async_engine(
            settings.database_url, pool_pre_ping=True, echo=False
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self):
        """Encerra o pool de conexões."""
        await self.engine.dispose()

    async def _create_database_if_not_exists(self):
        """Conecta ao banco 'postgres' padrão para criar o banco do bot, se necessário."""
        admin_url = settings.database_url.replace(
            f"/{settings.POSTGRES_DB}", "/postgres"
        )
        temp_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

        async with temp_engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}'"
                )
            )
            exists = result.scalar()

            if not exists:
                logger.info(
                    f"[Database] Banco '{settings.POSTGRES_DB}' não encontrado. Criando..."
                )
                await conn.execute(text(f'CREATE DATABASE "{settings.POSTGRES_DB}"'))

        await temp_engine.dispose()

    async def setup_database(self):
        """Verifica conexão e sincroniza schemas."""
        try:
            await self._create_database_if_not_exists()

            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                await conn.run_sync(Base.metadata.create_all)

            logger.info("[Database] Conexão estabelecida e tabelas sincronizadas!")
        except Exception as e:
            logger.exception(f"[Database] Erro Crítico no Startup: {e}")
            raise e


db_client = PostgresClient()


async def get_db_session():
    async with db_client.session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
