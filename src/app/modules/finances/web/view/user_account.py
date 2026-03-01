from fastapi import APIRouter, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.finances.database import get_db_session
from app.modules.finances.repository import UserRepository, AccountRepository

router = APIRouter()

TEMPLATE_PATH = "finances/user/accounts/"


@router.get("/user/{user_id}/accounts", response_class=HTMLResponse)
async def user_accounts_view(
    request: Request, user_id: str, db: AsyncSession = Depends(get_db_session)
):
    user_repo = UserRepository(db)
    try:
        user, owned_accounts, available_accounts = await user_repo.get_accounts(user_id)
    except ValueError:
        return RedirectResponse(url="/finance?error=Usuário não encontrado")

    return request.app.state.templates.TemplateResponse(
        TEMPLATE_PATH + "accounts.j2",
        {
            "request": request,
            "user": user,
            "owned_accounts": sorted(owned_accounts, key=lambda x: x.name),
            "available_accounts": available_accounts,
        },
    )


@router.post("/user/{user_id}/accounts/{account_id}", response_class=HTMLResponse)
async def add_account_to_user(
    request: Request,
    user_id: str,
    account_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    user_repo = UserRepository(db)
    try:
        _, account = await user_repo.add_account(user_id, account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return request.app.state.templates.TemplateResponse(
        TEMPLATE_PATH + "partials/account_card_fragment.j2",
        {"request": request, "acc": account, "user_id": user_id},
    )


@router.delete("/user/{user_id}/accounts/{account_id}", response_class=HTMLResponse)
async def remove_account_from_user(
    request: Request,
    user_id: str,
    account_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    user_repo = UserRepository(db)
    try:
        user, account = await user_repo.remove_account(user_id, account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user.accounts:
        return request.app.state.templates.TemplateResponse(
            TEMPLATE_PATH + "partials/empty_accounts.j2",
            {"request": request, "acc": account, "user_id": user_id},
        )

    return request.app.state.templates.TemplateResponse(
        "finances/user/accounts/partials/menu_item.j2",
        {"request": request, "acc": account, "user_id": user_id},
    )


@router.get(
    "/user/{user_id}/accounts/{account_id}/edit-form", response_class=HTMLResponse
)
async def edit_balance_form(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    account_repo = AccountRepository(db)
    account = await account_repo.get(account_id)
    return request.app.state.templates.TemplateResponse(
        TEMPLATE_PATH + "partials/balance_edit_form.j2",
        {"request": request, "acc": account},
    )


@router.get("/user/{user_id}/accounts/{account_id}", response_class=HTMLResponse)
async def edit_balance_form(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    account_repo = AccountRepository(db)
    account = await account_repo.get(account_id)
    return request.app.state.templates.TemplateResponse(
        TEMPLATE_PATH + "partials/balance_display.j2",
        {"request": request, "acc": account},
    )


@router.patch("/user/{user_id}/accounts/{account_id}", response_class=HTMLResponse)
async def edit_balance(
    request: Request,
    account_id: int,
    initial_balance: float = Form(...),
    db: AsyncSession = Depends(get_db_session),
):
    account_repo = AccountRepository(db)

    try:
        cents = int(round(initial_balance * 100))
        account = await account_repo.edit(account_id, {"initial_balance_cents": cents})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return request.app.state.templates.TemplateResponse(
        TEMPLATE_PATH + "partials/balance_display.j2",
        {"request": request, "acc": account},
    )
