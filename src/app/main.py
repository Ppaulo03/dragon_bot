import uvicorn
from contextlib import asynccontextmanager
from loguru import logger
from pathlib import Path

from app.config import settings
from app.infrastructure import storage
from app.infrastructure.providers import PROVIDERS, PROVIDERS_ROUTERS

from app.core.services.factory import TriggerFactory
from app.core import trigger_manager

from app.infrastructure.database import db_client
from app.infrastructure import webhooks_router
from app.web import web_router

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida do App: Inicializa recursos no boot e limpa no shutdown.
    """
    logger.info("Iniciando o Boot do Bot...")
    try:

        await storage.setup()
        import app.core.logic.response_impl as responses_impl

        _ = responses_impl

        await db_client.setup_database()
        for provider in PROVIDERS.values():
            await provider.initialize()

        factory = TriggerFactory(storage_service=storage)
        primary, fallback = await factory.load_triggers()

        for trigger in primary:
            trigger_manager.register(trigger, is_primary=True)
        for trigger in fallback:
            trigger_manager.register(trigger, is_primary=False)

        logger.info(
            f"Bot pronto! {len(primary)} triggers e {len(fallback)} fallbacks ativos."
        )

        yield

    finally:
        logger.info("Desligando recursos...")
        await db_client.close()
        for provider in PROVIDERS.values():
            if hasattr(provider, "close") and callable(provider.close):
                await provider.close()


app = FastAPI(title="Dragon Bot", lifespan=lifespan)

CURRENT_DIR = Path(__file__).parent
STATIC_DIR = CURRENT_DIR / "web" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    logger.warning(f"Pasta static não encontrada em {STATIC_DIR}")


app.include_router(webhooks_router)
app.include_router(web_router)
for router in PROVIDERS_ROUTERS:
    app.include_router(router)


@app.get("/")
async def root():
    status = {}
    for provider_name, provider in PROVIDERS.items():
        status[provider_name] = await provider.check_status()
    return {"message": "Dragon Bot is running!", "providers": status}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=settings.DEBUG)
