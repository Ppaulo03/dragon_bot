from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from loguru import logger

from app.config import settings
from app.core.services import TriggerManager
from app.infrastructure.providers.evolution import (
    EvolutionWebhook,
    process_evolution_message,
)

router = APIRouter(prefix="/evolution", tags=["Evolution"])


@router.post("")
async def handle_evolution_webhook(
    data: EvolutionWebhook,
    background_tasks: BackgroundTasks,
    manager: TriggerManager = Depends(TriggerManager),
):

    if (
        settings.EVOLUTION_INSTANCE_TOKEN
        and data.apikey != settings.EVOLUTION_INSTANCE_TOKEN
    ):
        logger.warning("Tentativa de acesso não autorizada. API Key inválida.")
        raise HTTPException(status_code=403, detail="Acesso negado")

    if data.data.key.from_me:
        return {"status": "ignored"}

    try:
        message_data = process_evolution_message(data)
    except Exception as e:
        logger.error(f"Erro ao adaptar mensagem da Evolution: {e}")
        return {"status": "error", "detail": "failed to parse message"}

    background_tasks.add_task(manager.process, message_data)
    return {"status": "received"}
