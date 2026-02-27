from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ContactPayload(BaseModel):
    full_name: str
    wuid: str
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class ChatResponse(BaseModel):
    id: str
    status: str
    metadata: Optional[Dict[str, Any]] = None


class ChatClient(ABC):
    @abstractmethod
    async def send_text(
        self, instance: str, number: str, text: str, **options
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def send_media(
        self,
        instance: str,
        number: str,
        media: str,
        media_type: MediaType,
        mime_type: str,
        **options,
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def send_audio(
        self, instance: str, number: str, audio: str, **options
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def send_sticker(
        self, instance: str, number: str, sticker: str, **options
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def send_contact(
        self, instance: str, number: str, contacts: List[ContactPayload]
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def check_status(self) -> str:
        pass
