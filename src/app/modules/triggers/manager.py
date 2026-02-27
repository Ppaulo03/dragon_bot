from typing import List, Optional
from loguru import logger
from app.kernel import MessageData
from .core.event import TriggerEvent


class TriggerManager:
    _instance: Optional["TriggerManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.primary_triggers: List[TriggerEvent] = []
        self.fallback_triggers: List[TriggerEvent] = []

        self._initialized = True
        logger.info("TriggerManager inicializado como Singleton.")

    def register(self, trigger: TriggerEvent, is_primary: bool = True) -> None:
        target_list = self.primary_triggers if is_primary else self.fallback_triggers
        target_list.append(trigger)
        logger.debug(
            f"Gatilho '{trigger.name}' registrado como {'Primário' if is_primary else 'Fallback'}."
        )

    async def process(self, msg_data: MessageData) -> None:
        if await self._run_events(self.primary_triggers, msg_data, "Primary"):
            return
        await self._run_events(self.fallback_triggers, msg_data, "Fallback")

    async def _run_events(
        self, triggers: List[TriggerEvent], msg: MessageData, label: str
    ) -> bool:
        for trigger in triggers:
            try:
                if await trigger.is_match(msg):
                    if await trigger.execute(msg):
                        logger.success(f"[{label}] Evento executado: {trigger.name}")
                        return True
            except Exception as e:
                logger.error(f"Erro ao processar gatilho '{trigger.name}': {e}")
        return False


trigger_manager = TriggerManager()
