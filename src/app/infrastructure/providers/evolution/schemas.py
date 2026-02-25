from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvolutionBaseModel(BaseModel):
    """Base para todos os schemas da Evolution para evitar repetição."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class MessageKey(EvolutionBaseModel):
    remote_jid: str = Field(..., alias="remoteJid")
    from_me: bool = Field(..., alias="fromMe")
    id: str
    participant: Optional[str] = None
    addressing_mode: Optional[str] = Field(None, alias="addressingMode")


class EvoMessageData(EvolutionBaseModel):
    key: MessageKey

    message: Optional[Dict[str, Any]] = None
    message_type: Optional[str] = Field(None, alias="messageType")
    push_name: Optional[str] = Field(None, alias="pushName")
    message_timestamp: Optional[int] = Field(None, alias="messageTimestamp")


class EvolutionWebhook(EvolutionBaseModel):
    event: str
    instance: str
    data: EvoMessageData
    apikey: str
