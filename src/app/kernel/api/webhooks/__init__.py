from fastapi import APIRouter
from .evolution import router as evolution_router

router = APIRouter(prefix="/webhook", tags=["Webhooks"])
router.include_router(evolution_router)

__all__ = ["router"]
