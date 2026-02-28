import re
from sqlalchemy import insert, delete, select, update
from fastapi import APIRouter, Body, Form, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import (
    Account,
    Category,
    User,
    user_accounts,
    Transaction,
)

router = APIRouter(prefix="/api/internal/finance", tags=["Finance API"])


@router.post("/users")
async def api_add_user(
    name: str = Form(...),
    jid: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
):
    clean_id = re.sub(r"\D", "", jid)

    try:
        existing = await db.get(User, clean_id)
        if existing:
            raise ValueError(
                f"O número {clean_id} já está vinculado ao perfil '{existing.name}'."
            )

        new_user = User(id=clean_id, name=name)
        db.add(new_user)
        await db.commit()
        return RedirectResponse(url="/finance", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as e:
        return RedirectResponse(
            url=f"/finance?error={str(e)}", status_code=status.HTTP_303_SEE_OTHER
        )


@router.delete("/users/{user_id}")
async def api_delete_user(user_id: str, db: AsyncSession = Depends(get_db_session)):
    """API para deletar usuário"""
    user = await db.get(User, user_id)
    if user:
        await db.delete(user)
        await db.commit()
        return {"message": "Usuário removido"}
    return JSONResponse(status_code=404, content={"message": "Não encontrado"})


@router.post("/user/{user_id}/link/{account_id}")
async def api_link_account(
    user_id: str, account_id: int, db: AsyncSession = Depends(get_db_session)
):
    stmt = insert(user_accounts).values(user_id=user_id, account_id=account_id)

    try:
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        return {"status": "already_linked", "error": str(e)}

    return {"status": "linked"}


@router.delete("/user/{user_id}/unlink/{account_id}")
async def api_unlink_account(
    user_id: str, account_id: int, db: AsyncSession = Depends(get_db_session)
):
    stmt = delete(user_accounts).where(
        user_accounts.c.user_id == user_id, user_accounts.c.account_id == account_id
    )

    await db.execute(stmt)
    await db.commit()

    return {"status": "unlinked"}


@router.patch("/accounts/{account_id}")
async def api_update_account(
    account_id: int, data: dict = Body(...), db: AsyncSession = Depends(get_db_session)
):
    account = await db.get(Account, account_id)
    if not account:
        return {"status": "error", "message": "Conta não encontrada"}, 404

    if "initial_balance" in data:
        try:
            raw_value = str(data["initial_balance"]).replace(",", ".")
            account.initial_balance_cents = int(float(raw_value) * 100)
        except ValueError:
            return {"status": "error", "message": "Valor inválido"}, 400
    await db.commit()
    return {"status": "success", "new_balance": account.initial_balance_cents}


@router.patch("/users/{user_id}")
async def api_update_user(
    user_id: str,
    name: str = Body(embed=True),
    db: AsyncSession = Depends(get_db_session),
):
    user = await db.get(User, user_id)
    if not user:
        return {"status": "error"}, 404

    user.name = name
    await db.commit()
    return {"status": "success"}


@router.delete("/users/{user_id}")
async def api_delete_user(user_id: str, db: AsyncSession = Depends(get_db_session)):
    user = await db.get(User, user_id)
    if user:
        await db.delete(user)
        await db.commit()
        return {"status": "success"}
    return {"status": "error"}, 404


@router.get("/categories")
async def get_categories(
    parent_id=None,
    db: AsyncSession = Depends(get_db_session),
):

    if not parent_id:
        return []

    query = select(Category).filter_by(parent_id=parent_id).order_by(Category.name)

    result = await db.execute(query)
    categories_objects = result.scalars().all()

    # Retorna um Array (importante para evitar o erro de forEach)
    return [{"id": cat.id, "name": cat.name} for cat in categories_objects]


@router.patch("/transactions/{tx_id}")
async def patch_transaction(
    tx_id: str, data: dict, db: AsyncSession = Depends(get_db_session)
):
    # 1. Busca a transação original para garantir que ela existe
    query = select(Transaction).filter_by(id=tx_id)
    result = await db.execute(query)
    tx = result.scalar_one_or_none()

    if not tx:
        return {"error": "Transação não encontrada"}, 404

    update_data = {}
    if "entity" in data:
        update_data["entity"] = data["entity"]

    if "category_id" in data:
        update_data["category_id"] = data["category_id"]
        update_data["is_category_automatic"] = False

    if not update_data:
        return {"message": "Nenhuma alteração enviada"}, 400

    # 3. Executa o Update no Banco
    stmt = update(Transaction).where(Transaction.id == tx_id).values(**update_data)

    await db.execute(stmt)
    await db.commit()

    # 4. Retorna Sucesso para disparar o 'saved' no CSS
    return {"status": "success", "updated_fields": list(update_data.keys())}
