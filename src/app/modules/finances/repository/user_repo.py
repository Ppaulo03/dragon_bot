from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from sqlalchemy.orm import joinedload, selectinload
from ..database.models import User, Account
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

    async def get_accounts(
        self, user_id: str
    ) -> Tuple[User, List[Account], List[Account]]:
        """Retorna as contas do usuário e as contas disponíveis para associação."""

        result = await self.db.execute(
            select(User).options(selectinload(User.accounts)).where(User.id == user_id)
        )

        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Usuário não encontrado.")

        owned_ids = [acc.id for acc in user.accounts]
        avaiable = select(Account).order_by(Account.name)
        if owned_ids:
            avaiable = avaiable.where(~Account.id.in_(owned_ids))
        available_accounts = (await self.db.execute(avaiable)).scalars().all()

        return (user, user.accounts, available_accounts)

    async def add_account(self, user_id: str, account_id: int) -> Tuple[User, Account]:
        stmt = select(User).options(joinedload(User.accounts)).where(User.id == user_id)

        result = await self.db.execute(stmt)
        user = result.unique().scalar_one_or_none()
        if not user:
            raise ValueError("Usuário não encontrado.")

        account = await self.db.get(Account, account_id)
        if not account:
            raise ValueError("Conta não encontrada.")

        if account in user.accounts:
            raise ValueError("Conta já associada ao usuário.")

        user.accounts.append(account)
        await self.db.commit()

        return user, account

    async def remove_account(
        self, user_id: str, account_id: int
    ) -> Tuple[User, Account]:
        result = await self.db.execute(
            select(User).options(selectinload(User.accounts)).where(User.id == user_id)
        )

        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Usuário não encontrado.")

        account = await self.db.get(Account, account_id)
        if not account:
            raise ValueError("Conta não encontrada.")

        if account not in user.accounts:
            raise ValueError("Conta não associada ao usuário.")

        user.accounts.remove(account)
        await self.db.commit()
        return user, account
