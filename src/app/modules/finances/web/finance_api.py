import uuid
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy import insert, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import (
    Account,
    Category,
    User,
    user_accounts,
    Transaction,
    Template,
)

router = APIRouter(prefix="/api/internal/finance", tags=["Finance API"])


@router.get("/")
async def health_check():
    return {"status": "ok", "message": "Finance API is running"}


async def get_current_user(
    x_device_id: str = Header(..., alias="X-Device-Id"),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    query = select(User).where(User.id == x_device_id, User.access_token == token)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token or device ID")

    return user


@router.post("/pair")
async def pair_device(
    payload: dict = Body(...),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db_session),
):
    if authorization != "Bearer convite-123":
        raise HTTPException(status_code=401, detail="Invalid pairing token")

    device_id = payload.get("device_id")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")

    user = await db.get(User, device_id)
    if not user:
        new_token = str(uuid.uuid4())
        user = User(
            id=device_id, name=f"Device {device_id[:8]}", access_token=new_token
        )
        db.add(user)

        # 2. Link to master user's accounts (for now, we'll use the first user in the DB as master)
        master_query = select(User).limit(1)
        master_result = await db.execute(master_query)
        master_user = master_result.scalar_one_or_none()

        if master_user:
            # Get master user's accounts
            accounts_query = (
                select(Account)
                .join(user_accounts)
                .where(user_accounts.c.user_id == master_user.id)
            )
            accounts_result = await db.execute(accounts_query)
            accounts = accounts_result.scalars().all()

            for acc in accounts:
                stmt = insert(user_accounts).values(
                    user_id=device_id, account_id=acc.id
                )
                await db.execute(stmt)

        await db.commit()

    return {"access_token": user.access_token, "server_id": user.id}


@router.post("/sync/templates")
async def sync_templates(
    data: dict = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    local_id = data.get("id")
    name = data.get("name")

    query = select(Template).where(Template.local_id == local_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    if not template:
        template = Template(
            name=name,
            local_id=local_id,
            delimiter=data.get("delimiter", ";"),
            skip_rows=data.get("skip_rows", 1),
            csv_name_pattern=data.get("csv_name_pattern"),
            expected_header=data.get("expected_header"),
            date_column_index=data.get("date_column_index", 0),
            description_column_index=data.get("description_column_index", 1),
            amount_column_index=data.get("amount_column_index", 2),
            counterpart_column_index=data.get("counterpart_column_index"),
            date_format=data.get("date_format", "dd/MM/yyyy"),
            decimal_separator=data.get("decimal_separator", "."),
            is_income_positive=data.get("is_income_positive", True),
            is_deleted=data.get("is_deleted", False),
        )
        db.add(template)
    else:
        template.name = name
        template.delimiter = data.get("delimiter", template.delimiter)
        template.skip_rows = data.get("skip_rows", template.skip_rows)
        template.csv_name_pattern = data.get(
            "csv_name_pattern", template.csv_name_pattern
        )
        template.expected_header = data.get("expected_header", template.expected_header)
        template.date_column_index = data.get(
            "date_column_index", template.date_column_index
        )
        template.description_column_index = data.get(
            "description_column_index", template.description_column_index
        )
        template.amount_column_index = data.get(
            "amount_column_index", template.amount_column_index
        )
        template.counterpart_column_index = data.get(
            "counterpart_column_index", template.counterpart_column_index
        )
        template.date_format = data.get("date_format", template.date_format)
        template.decimal_separator = data.get(
            "decimal_separator", template.decimal_separator
        )
        template.is_income_positive = data.get(
            "is_income_positive", template.is_income_positive
        )
        template.is_deleted = data.get("is_deleted", template.is_deleted)

    await db.commit()
    return {"server_id": template.id}


@router.post("/sync/accounts")
async def sync_accounts(
    data: dict = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    local_id = data.get("id")
    name = data.get("name")
    balance = data.get("initial_balance_cents", 0)
    local_template_id = data.get("default_template_id")

    # Resolve Template ID
    template_id = None
    if local_template_id:
        t_query = select(Template).where(Template.local_id == local_template_id)
        t_result = await db.execute(t_query)
        template = t_result.scalar_one_or_none()
        if template:
            template_id = template.id

    # Search for existing account by local_id for this user
    query = (
        select(Account)
        .join(user_accounts)
        .where(user_accounts.c.user_id == user.id, Account.local_id == local_id)
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        account = Account(
            name=name,
            initial_balance_cents=balance,
            local_id=local_id,
            default_template_id=template_id,
            is_deleted=data.get("is_deleted", False),
        )
        db.add(account)
        await db.flush()  # Get the ID

        # Link to user
        stmt = insert(user_accounts).values(user_id=user.id, account_id=account.id)
        await db.execute(stmt)
    else:
        account.name = name
        account.initial_balance_cents = balance
        account.default_template_id = template_id
        account.is_deleted = data.get("is_deleted", account.is_deleted)

    await db.commit()
    return {"server_id": account.id}


@router.post("/sync/categories")
async def sync_categories(
    data: dict = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    cat_id = data.get("id")
    name = data.get("name")

    category = await db.get(Category, cat_id)
    if not category:
        category = Category(
            id=cat_id,
            name=name,
            color_hex=data.get("color_hex", 0),
            icon_name=data.get("icon_name", "category"),
            transaction_type=data.get("transaction_type", "expense"),
            level=data.get("level", 1),
            parent_id=data.get("parent_id"),
            is_deleted=data.get("is_deleted", False),
        )
        db.add(category)
    else:
        category.name = name
        category.color_hex = data.get("color_hex", category.color_hex)
        category.is_deleted = data.get("is_deleted", category.is_deleted)

    await db.commit()
    return {"server_id": category.id}


@router.post("/sync/transactions")
async def sync_transactions(
    data: dict = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    tx_id = data.get("id")
    local_account_id = data.get("account_id")
    category_id = data.get("category_id")

    # Resolve Account
    acc_query = select(Account).where(Account.local_id == local_account_id)
    acc_result = await db.execute(acc_query)
    account = acc_result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=400, detail=f"Account {local_account_id} not found"
        )

    transaction = await db.get(Transaction, tx_id)
    if not transaction:
        transaction = Transaction(
            id=tx_id,
            entity=data.get("entity", ""),
            description=data.get("description", ""),
            amount_cents=data.get("amount_cents", 0),
            date_timestamp=data.get("date_timestamp", 0),
            account_id=account.id,
            category_id=category_id,
            is_deleted=data.get("is_deleted", False),
            importation_id="cloud_sync",
        )
        db.add(transaction)
    else:
        transaction.entity = data.get("entity", transaction.entity)
        transaction.description = data.get("description", transaction.description)
        transaction.amount_cents = data.get("amount_cents", transaction.amount_cents)
        transaction.category_id = category_id
        transaction.is_deleted = data.get("is_deleted", transaction.is_deleted)

    await db.commit()
    return {"server_id": transaction.id}


@router.get("/sync/delta")
async def sync_delta(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # Order: Templates -> Accounts -> Categories -> Transactions

    # 1. Get Templates (active only)
    tmplt_query = select(Template).where(Template.is_deleted == False)
    tmplt_result = await db.execute(tmplt_query)
    templates = tmplt_result.scalars().all()

    # 2. Get User Accounts
    acc_query = (
        select(Account)
        .join(user_accounts)
        .where(user_accounts.c.user_id == user.id, Account.is_deleted == False)
    )
    acc_result = await db.execute(acc_query)
    accounts = acc_result.scalars().all()
    account_ids = [a.id for a in accounts]

    # 3. Get Categories (active only)
    cat_query = select(Category).where(Category.is_deleted == False)
    cat_result = await db.execute(cat_query)
    categories = cat_result.scalars().all()

    # 4. Get Transactions for these accounts
    tx_query = select(Transaction).where(
        Transaction.account_id.in_(account_ids), Transaction.is_deleted == False
    )
    tx_result = await db.execute(tx_query)
    transactions = tx_result.scalars().all()
    return {
        "templates": [
            {
                "id": t.local_id or str(t.id),
                "server_id": t.id,
                "name": t.name,
                "delimiter": t.delimiter,
                "skip_rows": t.skip_rows,
                "csv_name_pattern": t.csv_name_pattern,
                "expected_header": t.expected_header,
                "date_column_index": t.date_column_index,
                "description_column_index": t.description_column_index,
                "amount_column_index": t.amount_column_index,
                "counterpart_column_index": t.counterpart_column_index,
                "date_format": t.date_format,
                "decimal_separator": t.decimal_separator,
                "is_income_positive": t.is_income_positive,
                "is_deleted": t.is_deleted,
            }
            for t in templates
        ],
        "accounts": [
            {
                "id": a.local_id or str(a.id),
                "server_id": a.id,
                "name": a.name,
                "initial_balance_cents": a.initial_balance_cents,
                "default_template_id": (
                    next(
                        (
                            t.local_id
                            for t in templates
                            if t.id == a.default_template_id
                        ),
                        None,
                    )
                    if a.default_template_id
                    else None
                ),
                "is_deleted": a.is_deleted,
            }
            for a in accounts
        ],
        "categories": [
            {
                "id": c.id,
                "server_id": c.id,
                "name": c.name,
                "color_hex": c.color_hex,
                "icon_name": c.icon_name,
                "transaction_type": c.transaction_type,
                "level": c.level,
                "parent_id": c.parent_id,
                "is_deleted": c.is_deleted,
            }
            for c in categories
        ],
        "transactions": [
            {
                "id": t.id,
                "server_id": t.id,
                "entity": t.entity,
                "description": t.description,
                "amount_cents": t.amount_cents,
                "date_timestamp": t.date_timestamp,
                "account_id": accounts[account_ids.index(t.account_id)].local_id
                or str(t.account_id),
                "category_id": t.category_id,
                "is_deleted": t.is_deleted,
            }
            for t in transactions
        ],
    }


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
    if not account or account.is_deleted:
        return {"status": "error", "message": "Conta não encontrada"}, 404

    if "initial_balance" in data:
        try:
            raw_value = str(data["initial_balance"]).replace(",", ".")
            account.initial_balance_cents = int(float(raw_value) * 100)
        except ValueError:
            return {"status": "error", "message": "Valor inválido"}, 400
    await db.commit()
    return {
        "status": "success",
        "new_balance": account.initial_balance_cents,
        "server_id": account.id,
    }


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
    return {"status": "success", "server_id": user_id}


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
    parent_id: Optional[str] = None,
    tx_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    query = select(Category).where(Category.is_deleted == False)

    if parent_id:
        query = query.where(Category.parent_id == parent_id)
    else:
        # Busca raízes
        query = query.where(Category.parent_id == None)

    if tx_type:
        query = query.where(Category.transaction_type == tx_type)

    query = query.order_by(Category.name)

    result = await db.execute(query)
    categories_objects = result.scalars().all()

    # Retorna um Array (importante para evitar o erro de forEach)
    return [
        {"id": cat.id, "name": cat.name, "server_id": cat.id}
        for cat in categories_objects
    ]


@router.patch("/transactions/{tx_id}")
async def patch_transaction(
    tx_id: str, data: dict, db: AsyncSession = Depends(get_db_session)
):
    # 1. Busca a transação original para garantir que ela existe
    query = select(Transaction).filter_by(id=tx_id)
    result = await db.execute(query)
    tx = result.scalar_one_or_none()

    if not tx or tx.is_deleted:
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
    return {
        "status": "success",
        "updated_fields": list(update_data.keys()),
        "server_id": tx_id,
    }
