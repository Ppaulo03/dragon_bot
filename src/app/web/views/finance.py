from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import not_, select
from pathlib import Path
from app.infrastructure.database.postgrees_client import get_db_session
from src.app.infrastructure.database.models import User
from src.app.infrastructure.database.models import Account, user_accounts

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
router = APIRouter(prefix="/finance", tags=["Finance Management"])


@router.get("", response_class=HTMLResponse)
async def users_view(
    request: Request, error: str = None, db: AsyncSession = Depends(get_db_session)
):
    """Página de Seleção de Usuário (Navegador)"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return templates.TemplateResponse(
        "finance/users_list.j2",
        {"request": request, "users": users, "error": error},
    )


@router.get("/user/{user_id}/accounts", response_class=HTMLResponse)
async def user_accounts_view(
    request: Request, user_id: str, db: AsyncSession = Depends(get_db_session)
):

    user = await db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/finance?error=Usuário não encontrado")

    stmt_owned = (
        select(Account)
        .join(user_accounts, Account.id == user_accounts.c.account_id)
        .where(user_accounts.c.user_id == user_id)
    )
    owned_accounts = (await db.execute(stmt_owned)).scalars().all()

    # 3. Busca as contas que ele AINDA NÃO POSSUI (para vincular)
    owned_ids = [acc.id for acc in owned_accounts]
    stmt_available = (
        select(Account).where(not_(Account.id.in_(owned_ids)))
        if owned_ids
        else select(Account)
    )
    available_accounts = (await db.execute(stmt_available)).scalars().all()

    return templates.TemplateResponse(
        "finance/user_accounts.j2",
        {
            "request": request,
            "user": user,
            "owned_accounts": owned_accounts,
            "available_accounts": available_accounts,
        },
    )
