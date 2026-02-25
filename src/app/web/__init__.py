from fastapi import APIRouter
from .api import router as api_router
from .views import router as views_router

web_router = APIRouter()
web_router.include_router(api_router)
web_router.include_router(views_router)
