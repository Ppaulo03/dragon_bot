from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import not_, select

from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import User, Account

router = APIRouter()


@router.get("/user/{user_id}/accounts", response_class=HTMLResponse)
async def user_accounts_view(
    request: Request, user_id: str, db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(
        select(User).options(selectinload(User.accounts)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return RedirectResponse(url="/finance?error=Usuário não encontrado")
    owned_accounts = user.accounts
    owned_ids = [acc.id for acc in owned_accounts]
    stmt_available = select(Account).order_by(Account.name)
    if owned_ids:
        stmt_available = stmt_available.where(not_(Account.id.in_(owned_ids)))
    available_accounts = (await db.execute(stmt_available)).scalars().all()
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "finances/user/accounts/accounts.j2",
        {
            "request": request,
            "user": user,
            "owned_accounts": sorted(owned_accounts, key=lambda x: x.name),
            "available_accounts": available_accounts,
            "options": {},
        },
    )
