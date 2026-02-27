from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger

from app.kernel import settings
from app.kernel.core import module_registry
from app.kernel.api import router as api_router
from app.kernel.utils.views import setup_views
from app.kernel.infrastructure.providers import PROVIDERS, router as providers_router
from app.modules import setup_modules

setup_modules()
active_modules = module_registry.get_all()


@asynccontextmanager
async def lifespan(app: FastAPI):

    for provider in PROVIDERS:
        await provider.initialize()

    for module in active_modules:
        await module.startup(app)
        logger.info(f"[Lifespan] Módulo '{module.name}' iniciado.")

    logger.info(
        "[Lifespan] Todos os módulos iniciados. "
        "Aplicação pronta para receber mensagens."
    )
    yield

    for module in active_modules:
        await module.shutdown(app)
        logger.info(f"[Lifespan] Módulo '{module.name}' desligado.")

    for provider in PROVIDERS:
        await provider.close()

    logger.info("[Lifespan] Aplicação encerrada.")


app = FastAPI(title="Dragon Bot", lifespan=lifespan)
templates = setup_views(app)
app.state.templates = templates

app.include_router(api_router)
app.include_router(providers_router)
for module in module_registry.get_all():
    router = module.register_routes()
    if router:
        app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Dragon Bot is running!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=settings.DEBUG)
