from ..interfaces import MessageData, ChatResponse
from ..registry import response_registry
from typing import Any


@response_registry.register("send_text")
async def send_text(msg_data: MessageData, text: str, **options: Any) -> ChatResponse:
    return await msg_data.reply_text(text, **options)


@response_registry.register("send_audio")
async def send_audio(
    msg_data: MessageData, audio_url: str, **options: Any
) -> ChatResponse:
    return await msg_data.reply_audio(audio_url, **options)


@response_registry.register("send_sticker")
async def send_sticker(
    msg_data: MessageData, sticker_url: str, **options: Any
) -> ChatResponse:
    return await msg_data.reply_sticker(sticker_url, **options)


@response_registry.register("send_contact")
async def send_contact(
    msg_data: MessageData, contact_info: str, **options: Any
) -> ChatResponse:
    return await msg_data.reply_contact(contact_info, **options)
