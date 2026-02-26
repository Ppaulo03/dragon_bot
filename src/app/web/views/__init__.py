from fastapi import APIRouter

from .trigger_config_view import router as trigger_config_router
from .finance import router as finance_router

router = APIRouter()
router.include_router(trigger_config_router)
router.include_router(finance_router)
