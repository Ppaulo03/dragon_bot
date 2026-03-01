from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database.models import User
from ..utils import clean_phone_number


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self) -> List[User]:
        result = await self.db.execute(select(User))
        return result.scalars().all()

    async def add(self, name: str, jid: str) -> User:
        clean_id = clean_phone_number(jid)
        existing = await self.db.get(User, clean_id)
        if existing:
            raise ValueError(
                f"O número {clean_id} já está vinculado ao perfil '{existing.name}'."
            )

        new_user = User(id=clean_id, name=name)
        self.db.add(new_user)
        await self.db.commit()
        return new_user
