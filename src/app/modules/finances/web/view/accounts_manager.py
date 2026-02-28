from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.finances.database.models import Account, Template, User
from app.modules.finances.database import get_db_session

router = APIRouter(prefix="/accounts")


@router.get("/", response_class=HTMLResponse)
async def manage_finance(request: Request, db: AsyncSession = Depends(get_db_session)):

    accounts_result = await db.execute(select(Account).order_by(Account.name))
    accounts = accounts_result.scalars().all()

    profiles_result = await db.execute(select(User).order_by(User.name))
    profiles = profiles_result.scalars().all()

    templates_result = await db.execute(select(Template).order_by(Template.name))
    templates = templates_result.scalars().all()

    print(
        {
            "request": request,
            "accounts": accounts,
            "profiles": profiles,
            "templates": templates,
        }
    )
    return request.app.state.templates.TemplateResponse(
        "accounts.j2",
        {
            "request": request,
            "accounts": accounts,
            "profiles": profiles,
            "templates": templates,
        },
    )


@router.get("/edit/{acc_id}")
async def edit_account_form(
    acc_id: int, request: Request, db: AsyncSession = Depends(get_db_session)
):
    # 1. Busca a conta com os usuários já carregados (joinedload é importante!)
    result = await db.execute(
        select(Account).options(joinedload(Account.users)).filter_by(id=acc_id)
    )
    account = result.unique().scalar_one_or_none()  # O segredo está no .unique()

    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    # 3. Buscamos os dados auxiliares para o formulário
    templates_res = await db.execute(select(Template))
    templates = templates_res.scalars().all()

    users_res = await db.execute(select(User).order_by(User.name))
    all_users = users_res.scalars().all()
    return request.app.state.templates.TemplateResponse(
        "partials/account_form.j2",
        {
            "request": request,
            "acc": account,
            "templates": templates,
            "all_users": all_users,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_account_form(
    request: Request, db: AsyncSession = Depends(get_db_session)
):
    # Buscamos as opções para preencher os selects/checkboxes
    templates_res = await db.execute(select(Template))
    templates = templates_res.scalars().all()

    users_res = await db.execute(select(User).order_by(User.name))
    all_users = users_res.scalars().all()

    return request.app.state.templates.TemplateResponse(
        "partials/account_form.j2",
        {
            "request": request,
            "acc": None,  # Indica que é uma conta nova
            "templates": templates,
            "all_users": all_users,
        },
    )


@router.post("/save")
async def save_account(
    name: str = Form(...),
    account_id: str = Form(None),
    db: AsyncSession = Depends(get_db_session),
):
    if account_id:
        # Edição de conta existente
        res = await db.execute(select(Account).filter_by(id=int(account_id)))
        acc = res.scalar_one()
        acc.name = name
    else:
        db.add(Account(name=name))

    await db.commit()
    return RedirectResponse(url="/finance/accounts", status_code=303)


@router.delete("/{acc_id}")
async def delete_account(acc_id: int, db: AsyncSession = Depends(get_db_session)):
    # O Cascade do seu modelo cuidará das transações
    await db.execute(delete(Account).where(Account.id == acc_id))
    await db.commit()
    return HTMLResponse(status_code=200)


@router.patch("/{acc_id}")
async def patch_account(
    acc_id: int, data: dict, db: AsyncSession = Depends(get_db_session)
):

    query = select(Account).filter_by(id=acc_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        return {"error": "Conta não encontrada"}, 404

    update_fields = {}
    if "name" in data:
        update_fields["name"] = data["name"]

    if "initial_balance_cents" in data:
        update_fields["initial_balance_cents"] = int(data["initial_balance_cents"])

    if "default_template_id" in data:
        update_fields["default_template_id"] = data["default_template_id"]

    if not update_fields:
        return {"message": "Nenhum dado para atualizar"}, 400

    # 3. Executa a atualização atômica
    stmt = update(Account).where(Account.id == acc_id).values(**update_fields)

    await db.execute(stmt)
    await db.commit()

    return {
        "status": "success",
        "account_id": acc_id,
        "updated": list(update_fields.keys()),
    }
