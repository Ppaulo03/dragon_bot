from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from sqlalchemy.orm import selectinload
from ..database.models import User, Account
from ..utils import clean_phone_number
from typing import Dict, Any


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, account_id: int) -> Account:
        account = await self.db.get(Account, account_id)
        if not account:
            raise ValueError("Conta não encontrada.")
        return account

    async def edit(self, account_id: int, update_fields: Dict[str, Any]) -> Account:
        account = await self.db.get(Account, account_id)
        if not account:
            raise ValueError("Conta não encontrada.")

        for field, value in update_fields.items():
            if hasattr(account, field):
                setattr(account, field, value)

        await self.db.commit()
        return account
