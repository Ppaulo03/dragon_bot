from unittest import result

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from sqlalchemy.orm import selectinload
from ..database.models import User, Account, Template
from ..utils import clean_phone_number
from typing import Dict, Any


class TemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_users_template(self, user_id: str) -> List[tuple[int, Template]]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.accounts).selectinload(Account.template))
            .where(User.id == user_id)
        )

        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Usuário não encontrado.")

        account_template_pairs = [
            (acc.id, acc.template) for acc in user.accounts if acc.template is not None
        ]

        return account_template_pairs
