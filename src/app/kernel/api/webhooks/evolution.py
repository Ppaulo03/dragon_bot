from fastapi import APIRouter, BackgroundTasks
from app.kernel.core.registry import module_registry
from app.kernel.infrastructure.providers.evolution import (
    EvolutionWebhook,
    process_evolution_message,
)

router = APIRouter(prefix="/evolution", tags=["Evolution Webhooks"])


@router.post("")
async def handle_evolution(
    payload: EvolutionWebhook, background_tasks: BackgroundTasks
):
    message_data = process_evolution_message(payload)
    if not message_data:
        return {"status": "ignored"}
    for module in module_registry.get_all():
        background_tasks.add_task(module.handle_message, message_data)
    return {"status": "ok"}
