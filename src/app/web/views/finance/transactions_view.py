import json
from typing import Optional, Union
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.postgrees_client import get_db_session
from src.app.infrastructure.database.models import (
    Category,
    Transaction,
    User,
    Account,
    user_accounts,
)
from .utils import templates

router = APIRouter()


@router.get("/user/{user_id}/transactions", response_class=HTMLResponse)
async def transactions_view(
    request: Request,
    user_id: str,
    page: int = 1,
    q: Optional[str] = None,
    account_id: Union[int, str, None] = None,
    db: AsyncSession = Depends(get_db_session),
):
    if account_id == "" or account_id is None:
        account_id = None
    else:
        try:
            account_id = int(account_id)
        except ValueError:
            account_id = None

    limit = 50
    offset = (page - 1) * limit
    acc_stmt = (
        select(Account).join(user_accounts).where(user_accounts.c.user_id == user_id)
    )
    accounts_info = (await db.execute(acc_stmt)).scalars().all()
    acc_ids = [acc.id for acc in accounts_info]

    if not acc_ids:
        user = await db.get(User, user_id)
        if not user:
            return RedirectResponse(url="/finance?error=Usuário não encontrado")
        return templates.TemplateResponse(
            "finance/transactions_list.j2",
            {
                "request": request,
                "user": user,
                "transactions": [],
                "accounts": [],
                "total_pages": 0,
                "current_page": 1,
            },
        )

    query = (
        select(Transaction)
        .options(joinedload(Transaction.account))
        .where(Transaction.account_id.in_(acc_ids))
    )

    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if q:
        query = query.where(
            or_(
                Transaction.entity.ilike(f"%{q}%"),
                Transaction.description.ilike(f"%{q}%"),
            )
        )

    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0

    res = await db.execute(
        query.order_by(Transaction.date_timestamp.desc()).limit(limit).offset(offset)
    )
    transactions = res.scalars().all()
    stmt_cats = select(Category).order_by(Category.name)
    all_cats = (await db.execute(stmt_cats)).scalars().all()
    cat_lv1 = [c for c in all_cats if c.level == 1]
    categories_json = json.dumps(
        [
            {"id": c.id, "name": c.name, "parent_id": c.parent_id, "level": c.level}
            for c in all_cats
        ]
    )
    user = await db.get(User, user_id)
    return templates.TemplateResponse(
        "finance/transactions_list.j2",
        {
            "request": request,
            "user": user,
            "transactions": transactions,
            "cat_lv1": cat_lv1,
            "categories_json": categories_json,
            "accounts": accounts_info,
            "current_acc": account_id,
            "current_q": q or "",
            "current_page": page,
            "total_pages": (total_count + limit - 1) // limit,
        },
    )
