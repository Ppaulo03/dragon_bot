from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import User

from .account_view import router as account_router
from .transactions_view import router as transactions_router
from .user_view import router as user_router

router = APIRouter(prefix="/finance", tags=["Finance Management"])


@router.get("", response_class=HTMLResponse)
async def users_view(
    request: Request, error: str = None, db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "users_list.j2",
        {"request": request, "users": users, "error": error},
    )


# Inclui os sub-roteadores
router.include_router(user_router)
router.include_router(account_router)
router.include_router(transactions_router)

__all__ = ["router"]
