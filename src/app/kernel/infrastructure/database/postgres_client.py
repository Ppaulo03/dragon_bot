from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from loguru import logger


class PostgresClient:
    def __init__(self, database_url: str, db_name: str):
        self.database_url = database_url
        self.db_name = db_name
        self.engine = create_async_engine(
            self.database_url, pool_pre_ping=True, echo=False
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def _create_database_if_not_exists(self):
        """Usa a URL administrativa para garantir que o banco do módulo existe."""
        admin_url = str(self.engine.url).replace(f"/{self.db_name}", "/postgres")
        temp_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

        async with temp_engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'")
            )
            if not result.scalar():
                logger.info(f"[Database] Criando banco '{self.db_name}'...")
                await conn.execute(text(f'CREATE DATABASE "{self.db_name}"'))

        await temp_engine.dispose()

    async def setup_database(self, base_metadata):
        """Verifica o banco e sincroniza as tabelas do módulo específico."""
        try:
            await self._create_database_if_not_exists()
            async with self.engine.begin() as conn:
                await conn.run_sync(base_metadata.create_all)
            logger.info(f"[Database] Banco '{self.db_name}' pronto e sincronizado!")
        except Exception as e:
            logger.exception(f"[Database] Erro ao inicializar '{self.db_name}': {e}")
            raise e

    async def close(self):
        await self.engine.dispose()
