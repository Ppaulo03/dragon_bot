from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, computed_field, field_validator
from .chat import ChatClient, ChatResponse, MediaType
from imagehash import ImageHash, hex_to_hash


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    CONTACT = "contact"

    @classmethod
    def all_values(cls):
        return [item.value for item in cls]


class MessageData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)

    message_id: str
    name: str
    number: str
    type: MessageType
    body: str
    instance: str
    is_group: bool
    mentioned: bool
    client: ChatClient

    cached_hash: Optional[ImageHash] = None
    cached_b64: Optional[str] = None

    @computed_field
    def is_media(self) -> bool:
        return self.type in ["image", "video", "audio", "document"]

    @computed_field
    def is_img(self) -> bool:
        return self.type in ["image", "sticker"]

    @field_validator("cached_hash", mode="before")
    def validate_cached_hash(cls, v):
        if isinstance(v, str):
            return hex_to_hash(v)
        return v

    async def reply_text(self, text: str, **options) -> ChatResponse:
        return await self.client.send_text(
            instance=self.instance, number=self.number, text=text, **options
        )

    async def reply_media(
        self,
        media: str,
        media_type: MediaType,
        mime_type: str,
        **options,
    ) -> ChatResponse:
        return await self.client.send_media(
            instance=self.instance,
            number=self.number,
            media=media,
            media_type=media_type,
            mime_type=mime_type,
            **options,
        )

    async def reply_audio(self, audio: str, **options) -> ChatResponse:
        return await self.client.send_audio(
            instance=self.instance, number=self.number, audio=audio, **options
        )

    async def reply_sticker(self, sticker: str, **options) -> ChatResponse:
        return await self.client.send_sticker(
            instance=self.instance, number=self.number, sticker=sticker, **options
        )

    async def reply_contact(self, contacts: list) -> ChatResponse:
        return await self.client.send_contact(
            instance=self.instance, number=self.number, contacts=contacts
        )
