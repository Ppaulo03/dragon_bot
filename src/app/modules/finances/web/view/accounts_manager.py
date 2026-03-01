from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

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
    initial_balance: float = Form(0.0),
    account_id: Optional[str] = Form(None),
    default_template_id: Optional[str] = Form(None),
    user_ids: List[str] = Form([]),
    db: AsyncSession = Depends(get_db_session),
):
    # 1. Preparação dos dados
    balance_cents = int(round(initial_balance * 100))
    template_id = (
        int(default_template_id)
        if default_template_id and default_template_id != ""
        else None
    )

    if account_id and account_id != "":
        # 1. Carregamos a conta já trazendo os usuários (selectinload é melhor que joinedload para N:N)
        stmt = (
            select(Account)
            .options(selectinload(Account.users))
            .filter_by(id=int(account_id))
        )
        res = await db.execute(stmt)
        acc = res.scalar_one_or_none()

        if not acc:
            raise HTTPException(status_code=404, detail="Conta não encontrada")

        acc.name = name
        acc.initial_balance_cents = balance_cents
        acc.default_template_id = template_id
    else:
        acc = Account(
            name=name,
            initial_balance_cents=balance_cents,
            default_template_id=template_id,
        )
        db.add(acc)
        # Importante: Para objetos novos, precisamos garantir que a lista de users exista
        acc.users = []

    # 2. Buscamos os usuários selecionados
    if user_ids:
        user_res = await db.execute(select(User).where(User.id.in_(user_ids)))
        new_users = list(user_res.scalars().all())
        acc.users = (
            new_users  # Agora o SQLAlchemy já tem acc.users na memória e não reclama
        )
    else:
        acc.users = []

    await db.commit()
    return RedirectResponse(url="/finance/accounts", status_code=303)


@router.delete("/{acc_id}")
async def delete_account(acc_id: str, db: AsyncSession = Depends(get_db_session)):
    account_id_int = int(acc_id)
    try:
        await db.execute(delete(Account).where(Account.id == account_id_int))
        await db.commit()
    except Exception as e:
        await db.rollback()
        return Response(status_code=500, content="Erro ao excluir a conta.")
    return Response(headers={"HX-Redirect": "/finance/accounts"})


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
