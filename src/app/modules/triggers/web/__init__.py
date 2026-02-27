from fastapi import APIRouter
from .trigger_api import router as api_router
from .trigger_view import router as views_router

web_router = APIRouter()
web_router.include_router(api_router)
web_router.include_router(views_router)

__all__ = ["web_router"]
