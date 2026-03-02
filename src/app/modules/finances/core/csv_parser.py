import csv
from datetime import datetime
import io
import re
from typing import Optional, List, Tuple
import uuid
from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session
from sqlalchemy.util import defaultdict
from ..database.models import Template, Transaction, Account
from ..repository import TemplateRepository


class FinanceService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def find_matching_template(
        self, user_id: str, filename: str
    ) -> Optional[Tuple[int, Template]]:
        """
        Tenta encontrar um template baseado no nome do arquivo ou no header.
        """
        template_repo = TemplateRepository(self.db)
        templates = await template_repo.get_users_template(user_id)
        for acc, tmpl in templates:
            if tmpl.csv_name_pattern and re.search(tmpl.csv_name_pattern, filename):
                return acc, tmpl

        return None

    def process_csv(
        self, content: bytes, template: Template, account_id: int
    ) -> List[Transaction]:
        """
        Lógica de parsing do CSV baseada nas configurações do Template.
        """
        text_content = content.decode("utf-8")
        f = io.StringIO(text_content)

        for _ in range(template.skip_rows):
            next(f)

        reader = csv.reader(f, delimiter=template.delimiter)
        transactions = []
        importation_id = str(uuid.uuid4())
        for row in reader:
            if not row:
                continue
            try:

                date_str = row[template.date_column_index].strip()
                date_str_clean = date_str.replace(" às ", " ").strip()
                clean_format = (
                    template.date_format.replace(" 'às' ", " ")
                    .replace(" às ", " ")
                    .replace("dd", "%d")
                    .replace("MM", "%m")
                    .replace("yyyy", "%Y")
                    .replace("yy", "%y")
                    .replace("HH", "%H")
                    .replace("mm", "%M")
                    .replace("ss", "%S")
                )

                dt = datetime.strptime(date_str_clean, clean_format)
                ts = int(dt.timestamp())

                raw_amount = row[template.amount_column_index].strip()

                if template.decimal_separator != ".":
                    raw_amount = raw_amount.replace(".", "")

                clean_amount = raw_amount.replace(template.decimal_separator, ".")
                clean_amount = "".join(
                    c for c in clean_amount if c.isdigit() or c in ".-"
                )
                amount_float = float(clean_amount)

                if not template.is_income_positive:
                    amount_float = -amount_float

                amount_cents = int(round(amount_float * 100))

                desc = row[template.description_column_index].strip()
                entity = "Desconhecido"
                if template.counterpart_column_index is not None:
                    entity = row[template.counterpart_column_index].strip()
                    if entity:
                        desc = f"{desc} - {entity}"

                txn = Transaction(
                    id=str(uuid.uuid4()),
                    description=desc,
                    amount_cents=amount_cents,
                    date_timestamp=ts,
                    account_id=account_id,
                    importation_id=importation_id,
                    is_category_automatic=True,
                )
                transactions.append(txn)

            except (ValueError, IndexError) as e:
                print(e)
                continue

        return transactions

    async def filter_duplicates(
        self, account_id: int, transactions: List[Transaction]
    ) -> List[Transaction]:
        if not transactions:
            return []

        incoming_groups = defaultdict(list)
        for tx in transactions:
            incoming_groups[(tx.date_timestamp, tx.amount_cents)].append(tx)

        filtered_transactions = []
        acc_id_int = int(account_id)
        for (dt_ts, amount), tx_list in incoming_groups.items():
            incoming_count = len(tx_list)

            stmt = select(func.count(Transaction.id)).where(
                Transaction.account_id == acc_id_int,
                Transaction.date_timestamp == tx.date_timestamp,
                Transaction.amount_cents == tx.amount_cents,
            )
            result = await self.db.execute(stmt)
            db_count = result.scalar() or 0

            if db_count >= incoming_count:
                continue

            filtered_transactions.extend(tx_list)
        return filtered_transactions
