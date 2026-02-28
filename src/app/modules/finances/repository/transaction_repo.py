from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Tuple, Sequence
from ..database.models import (
    Account,
    Transaction,
    Category,
    user_accounts,
)
from ..schemas import TransactionFilter


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_accounts(self, user_id: str) -> Sequence["Account"]:
        """Busca todas as contas vinculadas ao usuário através da tabela associativa."""
        stmt = (
            select(Account)
            .join(user_accounts)
            .where(user_accounts.c.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_transactions_with_count(
        self, user_id: str, acc_ids: List[int], filters: TransactionFilter
    ) -> Tuple[Sequence["Transaction"], int]:
        """
        Aplica filtros dinâmicos, paginação e retorna os dados junto com o total (count).
        """
        print(filters)
        # 1. Query Base
        query = (
            select(Transaction)
            .options(joinedload(Transaction.account))
            .where(Transaction.account_id.in_(acc_ids))
        )

        # 2. Filtros Dinâmicos
        if filters.account_id:
            query = query.where(Transaction.account_id == filters.account_id)

        if filters.q:
            search_filter = f"%{filters.q}%"
            query = query.where(
                or_(
                    Transaction.entity.ilike(search_filter),
                    Transaction.description.ilike(search_filter),
                )
            )

        if filters.start_timestamp:
            query = query.where(Transaction.date_timestamp >= filters.start_timestamp)

        if filters.end_timestamp:
            query = query.where(Transaction.date_timestamp <= filters.end_timestamp)

        # 3. Contagem Total (antes de aplicar limit/offset)
        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_stmt)).scalar() or 0

        # 4. Execução com Ordenação e Paginação
        res = await self.db.execute(
            query.order_by(Transaction.date_timestamp.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        transactions = res.scalars().all()

        return transactions, total_count

    async def get_all_categories(self):
        """Busca categorias para os selects do template."""
        stmt = select(Category).order_by(Category.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
