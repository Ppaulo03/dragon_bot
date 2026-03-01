from fastapi import APIRouter

from .index import router as index_router
from .user_account import router as user_account_router

from .transactions_view import router as transactions_router
from .user_view import router as user_router
from .accounts_manager import router as accounts_manager_router
from .templats_manager import router as templates_manager_router


router = APIRouter(prefix="/finance", tags=["Finance Management"])


# Inclui os sub-roteadores
router.include_router(index_router)
router.include_router(user_account_router)

router.include_router(user_router)
router.include_router(transactions_router)
router.include_router(accounts_manager_router)
router.include_router(templates_manager_router)


__all__ = ["router"]
