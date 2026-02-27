from random import choice, random
from typing import Any, Awaitable, Callable, List, Union, Optional, Dict

from app.kernel import MessageData, MessageType, ChatResponse
from app.kernel import response_registry
from .matchers import Matcher
from loguru import logger


async def send_text(msg_data: MessageData, text: str, **options: Any) -> ChatResponse:
    return await msg_data.reply_text(text, **options)


async def send_audio(
    msg_data: MessageData, audio_url: str, **options: Any
) -> ChatResponse:
    return await msg_data.reply_audio(audio_url, **options)


async def send_sticker(
    msg_data: MessageData, sticker_url: str, **options: Any
) -> ChatResponse:
    return await msg_data.reply_sticker(sticker_url, **options)


async def send_contact(
    msg_data: MessageData, contact_info: str, **options: Any
) -> ChatResponse:
    return await msg_data.reply_contact(contact_info, **options)


async def send_image(
    msg_data: MessageData,
    media_url: str,
    mime_type: str = "image/jpeg",
    **options: Any,
) -> ChatResponse:
    return await msg_data.reply_media(media_url, "image", mime_type, **options)


ACTIONS_REGISTRY = {
    "send_text": send_text,
    "send_audio": send_audio,
    "send_sticker": send_sticker,
    "send_contact": send_contact,
    "send_image": send_image,
}


class TriggerEvent:
    def __init__(
        self,
        name: str,
        chance: float,
        action_type: MessageType,
        choices: Union[List[str], Callable[[MessageData], Awaitable[str]]],
        matcher: Matcher,
        action_options: Dict[str, Any] = {},
    ):
        self.name = name
        self.chance = chance
        self.action_type = action_type
        self.choices = choices
        self.matcher = matcher
        self.action_options = action_options

    async def is_match(self, msg_data: MessageData) -> bool:
        """Verifica se o gatilho deve ser acionado."""
        if self.chance < 1.0 and random() >= self.chance:
            return False
        return await self.matcher.is_match(msg_data)

    async def execute(self, msg_data: MessageData) -> bool:
        selected = await self._resolve_choice(msg_data)
        if not selected:
            return False

        try:
            response: Optional[ChatResponse] = None
            response_handler = response_registry.get_handler(self.action_type)
            if response_handler:
                response = await response_handler(
                    msg_data, selected, **self.action_options
                )
            else:
                logger.warning(
                    f"Tipo de resposta {self.action_type} não suportado no gatilho {self.name}"
                )
                return False
            return response is not None and response.status == "success"

        except Exception as e:
            logger.exception(f"Erro ao executar o gatilho {self.name}: {e}")
            return False

    async def _resolve_choice(self, msg_data: MessageData) -> Optional[str]:
        if callable(self.choices):
            return await self.choices(msg_data)
        if isinstance(self.choices, list) and self.choices:
            return choice(self.choices)
        return str(self.choices) if self.choices else None
