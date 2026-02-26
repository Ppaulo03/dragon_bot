from fastapi import APIRouter
from .trigger_config import router as trigger_config_router
from .finance import router as finance_router

router = APIRouter(prefix="/api/internal")
router.include_router(trigger_config_router)
router.include_router(finance_router)
