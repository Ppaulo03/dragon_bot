import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import User
from ...schemas import TransactionFilter
from ...repository.transaction_repo import TransactionRepository

router = APIRouter()


@router.get("/user/{user_id}/transactions", response_class=HTMLResponse)
async def transactions_view(
    request: Request,
    user_id: str,
    filters: TransactionFilter = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    repo = TransactionRepository(db)

    # 1. Busca contas e valida existência do usuário
    accounts_info = await repo.get_user_accounts(user_id)
    acc_ids = [acc.id for acc in accounts_info]

    if not acc_ids:
        user = await db.get(User, user_id)
        if not user:
            return RedirectResponse(url="/finance?error=Usuário não encontrado")

        return request.app.state.templates.TemplateResponse(
            "transactions_list.j2",
            {
                "request": request,
                "user": user,
                "transactions": [],
                "accounts": [],
                "total_pages": 0,
                "current_page": filters.page,
            },
        )

    transactions, total_count = await repo.find_transactions_with_count(
        user_id, acc_ids, filters
    )
    all_cats = await repo.get_all_categories()

    cat_lv1 = [c for c in all_cats if c.level == 1]
    categories_json = json.dumps(
        [
            {"id": c.id, "name": c.name, "parent_id": c.parent_id, "level": c.level}
            for c in all_cats
        ]
    )
    user = await db.get(User, user_id)

    return request.app.state.templates.TemplateResponse(
        "transactions_list.j2",
        {
            "request": request,
            "user": user,
            "transactions": transactions,
            "cat_lv1": cat_lv1,
            "categories_json": categories_json,
            "accounts": accounts_info,
            "current_acc": filters.account_id,
            "current_q": filters.q or "",
            "current_page": filters.page,
            "total_pages": (total_count + filters.limit - 1) // filters.limit,
        },
    )
