from fastapi import APIRouter
from .evolution import router as evolution_router

webhooks_router = APIRouter(prefix="/webhooks")
webhooks_router.include_router(evolution_router)
__all__ = ["webhooks_router"]
