import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple
from loguru import logger
import json

from app.config import settings
from app.core.entities import TriggerEvent
from app.core.logic import MATCHER_REGISTRY, ACTION_REGISTRY
from app.infrastructure import storage


class TriggerFactory:
    def __init__(self, storage_service):
        """
        Recebe a instância de StorageService da Infrastructure.
        """
        self.storage = storage_service
        self.yaml_path = Path(settings.YAML_CONFIG_PATH)
        self.bucket_url = (
            f'{settings.BUCKET_ENDPOINT.rstrip("/")}/{settings.BUCKET_NAME.rstrip("/")}'
        )

    async def load_triggers(self) -> Tuple[List[TriggerEvent], List[TriggerEvent]]:
        if not self.yaml_path.exists():
            logger.warning(
                f"Arquivo de configuração '{self.yaml_path}' não encontrado. Nenhuma trigger carregada."
            )
            return [], []

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        return (
            await self._build_list(config.get("triggers", [])),
            await self._build_list(config.get("no_triggers", [])),
        )

    async def _build_list(self, items: List[Dict[str, Any]]) -> List[TriggerEvent]:
        events = []
        for item in items:
            event = await self._create_trigger(item)
            if event:
                events.append(event)
        return events

    async def _create_trigger(self, item: Dict[str, Any]) -> TriggerEvent | None:
        try:
            matcher_type = MATCHER_REGISTRY.get(item.get("matcher", "always"))
            if not matcher_type:
                logger.error(
                    f"Matcher '{item.get('matcher')}' não encontrado para trigger '{item.get('name')}'"
                )
                return None

            matcher = matcher_type(item.get("params", {}))
            action_name = item.get("action")
            if action_name in ACTION_REGISTRY:
                choices = ACTION_REGISTRY[action_name]
            else:
                choices = await self._resolve_choices(item)

            return TriggerEvent(
                name=item.get("name", "Unnamed"),
                chance=float(item.get("chance", 1.0)),
                action_type=item.get("type", "send_text"),
                choices=choices,
                matcher=matcher,
            )
        except Exception as e:
            logger.error(f"Erro ao criar trigger {item.get('name')}: {e}")
            return None

    async def _resolve_choices(self, item: Dict[str, Any]) -> List[Any]:
        """Resolve se o conteúdo vem de arquivo, URL do bucket ou valor direto."""
        action_type = item.get("type", "")
        files = item.get("files", [])
        value = [item.get("value", "")]
        if not files:
            return value

        if action_type in ["send_audio", "send_sticker", "send_image"]:
            return [self._format_url(f) for f in files]

        choices = []
        for file in files:
            if file.lower().endswith((".jpg", ".png", ".mp3", ".ogg", ".webp")):
                continue

            content = await self._read_from_storage(file)
            choices.extend(content)

        return choices or value

    def _format_url(self, path: str) -> str:

        if not path or path.startswith(("http://", "https://")):
            return path
        clean_path = path.lstrip("/")
        base_url = self.bucket_url.rstrip("/")
        return f"{base_url}/{clean_path}"

    async def _read_from_storage(self, filename: str) -> List[str]:
        if not filename:
            return []

        try:
            response = await storage.get_item_content(file_key=filename)
            if not response:
                logger.warning(f"Arquivo '{filename}' não encontrado no storage.")
                return []

            content = response.decode("utf-8")

            if filename.lower().endswith(".json"):
                data = json.loads(content)
                if isinstance(data, list):
                    return [str(item) for item in data]
                return [str(data)]
            return [content.strip()]

        except Exception as e:
            logger.warning(f"Falha ao ler arquivo '{filename}' no storage: {e}")
            return []
