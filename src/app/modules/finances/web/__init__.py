from fastapi import APIRouter
from .view import router as view_router
from .finance_api import router as api_router

web_router = APIRouter()
web_router.include_router(view_router)
web_router.include_router(api_router)

__all__ = ["web_router"]
