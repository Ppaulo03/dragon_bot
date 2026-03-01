from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import User

from .account_view import router as account_router
from .transactions_view import router as transactions_router
from .user_view import router as user_router
from .accounts_manager import router as accounts_manager_router
from .templats_manager import router as templates_manager_router
from .index import router as index_router

router = APIRouter(prefix="/finance", tags=["Finance Management"])


# Inclui os sub-roteadores
router.include_router(user_router)
router.include_router(account_router)
router.include_router(transactions_router)
router.include_router(accounts_manager_router)
router.include_router(templates_manager_router)
router.include_router(index_router)

__all__ = ["router"]
