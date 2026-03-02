import sys
import os
import asyncio


from src.app.modules.finances.core.csv_parser import FinanceService
from src.app.modules.finances.core.categorizer import CategorizerService
from src.app.modules.finances.repository import TemplateRepository
from src.app.modules.finances.database import client

# Configuração de Banco (Ajuste para seu .env ou use um sqlite de teste)


async def main(csv_path: str, user_id: str):
    async with client.session_factory() as db:
        # finance_service = FinanceService(db)
        categorizer = CategorizerService(model_path="volumes/models/finance_model.pkl")
        await categorizer.evaluate_model(db)
    return
    # try:
    #     with open(csv_path, "rb") as f:
    #         content = f.read()

    #     filename = os.path.basename(csv_path)
    #     template_info = await finance_service.find_matching_template(
    #         user_id, filename
    #     )
    #     if not template_info:
    #         print(f"❌ Nenhum template encontrado para {filename}")
    #         return
    #     account_id, template = template_info
    #     print(f"✅ Template identificado: {template.name}")
    #     raw_transactions = finance_service.process_csv(
    #         content, template, account_id
    #     )
    #     print(f"📊 Extraídas {len(raw_transactions)} transações do CSV.")
    #     new_transactions = await finance_service.filter_duplicates(
    #         account_id, raw_transactions
    #     )
    #     print(
    #         f"🛡️ Após filtro de duplicatas: {len(new_transactions)} novas transações."
    #     )

    #     for tx in new_transactions:
    #         prediction = categorizer.predict(tx.description)
    #         if prediction:
    #             tx.category_id = prediction
    #             tx.is_category_automatic = True

    # finally:
    #     await db.close()


if __name__ == "__main__":
    csv_path = "extrato_de_11-12-2025_ate_10-01-2026.csv"
    account_id = "5562985429500"
    asyncio.run(main(csv_path, account_id))
