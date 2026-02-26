from typing import Optional

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, not_, select
from pathlib import Path
from app.infrastructure.database.postgrees_client import get_db_session
from src.app.infrastructure.database.models import Category, Transaction, User
from src.app.infrastructure.database.models import Account, user_accounts

from datetime import datetime


def format_timestamp(ts):
    if not ts:
        return ""
    try:
        ts_float = float(ts)
        if ts_float > 32503680000:
            ts_float /= 1000

        return datetime.fromtimestamp(ts_float).strftime("%d/%m/%Y %H:%M")
    except (ValueError, OSError, OverflowError):
        return "Data Inválida"


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["timestamp_to_date"] = format_timestamp
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
        .order_by(Account.name)
    )
    owned_accounts = (await db.execute(stmt_owned)).scalars().all()
    owned_ids = [acc.id for acc in owned_accounts]
    stmt_available = select(Account)
    if owned_ids:
        stmt_available = stmt_available.where(not_(Account.id.in_(owned_ids)))

    stmt_available = stmt_available.order_by(Account.name)
    available_accounts = (await db.execute(stmt_available)).scalars().all()
    return templates.TemplateResponse(
        "finance/user_accounts.j2",
        {
            "request": request,
            "user": user,
            "owned_accounts": owned_accounts,
            "available_accounts": available_accounts,
            "options": {},  # Mantenha se o seu base.j2 ainda pedir isso
        },
    )


@router.get("/user/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_view(
    request: Request, user_id: str, db: AsyncSession = Depends(get_db_session)
):
    user = await db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/finance?error=Usuário não encontrado")

    return templates.TemplateResponse(
        "finance/user_edit.j2", {"request": request, "user": user, "options": {}}
    )


@router.get("/user/{user_id}/transactions", response_class=HTMLResponse)
async def transactions_view(
    request: Request,
    user_id: str,
    page: int = 1,
    q: Optional[str] = None,  # Busca por texto (Entidade/Descrição)
    account_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
):
    limit = 50  # Quantas transações por página
    offset = (page - 1) * limit

    user = await db.get(User, user_id)

    # 1. Pegar as contas do usuário para os filtros
    stmt_acc = select(user_accounts.c.account_id).where(
        user_accounts.c.user_id == user_id
    )
    acc_ids = (await db.execute(stmt_acc)).scalars().all()

    # 2. Query Base com Filtros
    query = select(Transaction).where(Transaction.account_id.in_(acc_ids))

    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if q:
        query = query.where(
            Transaction.entity.ilike(f"%{q}%")
        )  # Busca case-insensitive

    # 3. Contagem Total (para a paginação)
    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    total_pages = (total_count + limit - 1) // limit

    # 4. Execução com Paginação
    res = await db.execute(
        query.order_by(Transaction.date_timestamp.desc()).limit(limit).offset(offset)
    )
    transactions = res.scalars().all()

    # 5. Dados Auxiliares
    categories = (
        (await db.execute(select(Category).where(Category.level == 3))).scalars().all()
    )
    accounts_info = (
        (await db.execute(select(Account).where(Account.id.in_(acc_ids))))
        .scalars()
        .all()
    )

    return templates.TemplateResponse(
        "finance/transactions_list.j2",
        {
            "request": request,
            "user": user,
            "transactions": transactions,
            "categories": categories,
            "accounts": accounts_info,
            "current_acc": account_id,
            "current_q": q or "",
            "current_page": page,
            "total_pages": total_pages,
            "options": {},
        },
    )
