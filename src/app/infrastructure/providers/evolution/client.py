from typing import Any, Dict, List
from app.config import settings
from app.core.interfaces import ChatClient, ChatResponse, MediaType
from app.infrastructure.network import BaseHttpClient
from loguru import logger


class EvolutionClient(ChatClient, BaseHttpClient):
    def __init__(self):
        super().__init__(
            base_url=settings.EVOLUTION_URL,
            headers={
                "apikey": settings.EVOLUTION_TOKEN,
                "Content-Type": "application/json",
            },
            rate_limit_delay=0.05,
        )

    def _prepare_payload(self, **kwargs) -> Dict[str, Any]:
        """Remove campos nulos e centraliza a lógica de limpeza."""
        return {k: v for k, v in kwargs.items() if v is not None}

    async def send_text(
        self, instance: str, number: str, text: str, **options
    ) -> ChatResponse:
        payload = self._clean_payload(
            {
                "number": number,
                "text": text,
                "linkPreview": options.pop("link_preview", False),
                **options,
            }
        )
        return await self._execute_send(instance, "sendText", payload)

    async def send_media(
        self,
        instance: str,
        number: str,
        media: str,
        media_type: MediaType,
        mime_type: str,
        **options,
    ) -> ChatResponse:
        payload = self._clean_payload(
            {
                "number": number,
                "media": media,
                "mediaType": media_type.value,
                "mimeType": mime_type,
                "fileName": options.pop("file_name", "file"),
                **options,
            }
        )
        return await self._execute_send(instance, "sendMedia", payload)

    async def send_audio(
        self, instance: str, number: str, audio: str, **options
    ) -> ChatResponse:
        """
        Envia áudio formatado para WhatsApp (PTT).
        """
        if not audio.startswith("http"):
            audio = f"{settings.BUCKET_ENDPOINT}/{settings.BUCKET_NAME}/{audio}"
        payload = self._clean_payload({"number": number, "audio": audio, **options})
        return await self._execute_send(instance, "sendWhatsAppAudio", payload)

    async def send_sticker(
        self, instance: str, number: str, sticker: str, **options
    ) -> ChatResponse:
        """
        Envia figurinhas (WebP).
        """
        if sticker.startswith(";base64,"):
            sticker = sticker.split(";base64,")[1]
        elif not sticker.startswith("http"):
            sticker = f"{settings.BUCKET_ENDPOINT}/{settings.BUCKET_NAME}/{sticker}"
        payload = self._clean_payload({"number": number, "sticker": sticker, **options})
        return await self._execute_send(instance, "sendSticker", payload)

    async def send_contact(
        self, instance: str, number: str, contacts: List[Dict[str, Any]]
    ) -> ChatResponse:
        """
        Envia um ou mais cartões de contato.
        """
        payload = {
            "number": number,
            "contact": contacts,
        }
        return await self._execute_send(instance, "sendContact", payload)

    async def _execute_send(
        self, instance: str, path: str, payload: dict
    ) -> ChatResponse:
        """Centraliza o envio e converte para ChatResponse."""
        endpoint = f"message/{path}/{instance}"
        try:
            response = await self.post(endpoint, json=payload)
            return ChatResponse(
                status="success", id=str(response.get("key", {}).get("id"))
            )
        except Exception as e:
            return ChatResponse(status="error", id="err", error_message=str(e))

    def _clean_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove Nones e strings vazias que podem confundir a API."""
        return {k: v for k, v in data.items() if v not in [None, ""]}

    async def fetch_instance(self, instance: str) -> Dict[str, Any]:
        """Busca detalhes de uma instância específica."""
        try:
            endpoint = "instance/fetchInstances"
            response = await self.get(endpoint, params={"instanceName": instance})
            return response[0]
        except Exception as e:
            logger.error(f"Erro ao buscar instância {instance}: {e}")
            return {}

    async def create_instance(self, instance: str) -> Dict[str, Any]:
        """Cria uma nova instância."""
        try:
            endpoint = "instance/create"
            body = {
                "instanceName": instance,
                "integration": "WHATSAPP-BAILEYS",
                "alwaysOnline": True,
                "readMessages": True,
                "webhook": {
                    "enabled": True,
                    "url": settings.EVOLUTION_WEBHOOK_URL,
                    "byEvents": settings.EVOLUTION_WEBHOOK_BY_EVENTS,
                    "base64": settings.EVOLUTION_WEBHOOK_BASE64,
                    "events": settings.EVOLUTION_WEBHOOK_EVENTS.split(","),
                },
            }
            return await self.post(endpoint, json=body)
        except Exception as e:
            logger.error(f"Erro ao criar instância {instance}: {e}")
            return {}

    async def set_webhook(self, instance: str) -> Dict[str, Any]:
        """Configura o webhook para uma instância específica."""
        try:
            endpoint = f"webhook/set/{instance}"
            body = {
                "webhook": {
                    "enabled": True,
                    "url": settings.EVOLUTION_WEBHOOK_URL,
                    "webhookByEvents": settings.EVOLUTION_WEBHOOK_BY_EVENTS,
                    "webhookBase64": settings.EVOLUTION_WEBHOOK_BASE64,
                    "events": settings.EVOLUTION_WEBHOOK_EVENTS.split(","),
                }
            }

            return await self.post(endpoint, json=body)
        except Exception as e:
            logger.error(f"Erro ao configurar webhook da instância {instance}: {e}")
            return {}

    async def initialize(self) -> bool:
        logger.info("Inicializando EvolutionClient...")
        instance = await self.fetch_instance(settings.EVOLUTION_INSTANCE)
        if not instance:
            instance = await self.create_instance(settings.EVOLUTION_INSTANCE)
            instance_token = instance.get("hash")
        else:
            instance_token = instance.get("token")
            await self.set_webhook(settings.EVOLUTION_INSTANCE)
        settings.EVOLUTION_INSTANCE_TOKEN = instance_token

    async def check_status(self) -> str:
        """Verifica o status da instância."""
        endpoint = f"instance/connectionState/{settings.EVOLUTION_INSTANCE}"
        details = await self.get(endpoint)
        return details.get("instance", {}).get("state", "")

    async def get_qrcode(self) -> str:
        """Obtém o QR code para autenticação, se necessário."""
        endpoint = f"instance/connect/{settings.EVOLUTION_INSTANCE}"
        response = await self.get(endpoint)
        return response.get("base64", "")

    async def logout(self) -> bool:
        """Desconecta a instância, forçando nova autenticação."""
        try:
            endpoint = f"instance/logout/{settings.EVOLUTION_INSTANCE}"
            await self.delete(endpoint)
            return True
        except Exception as e:
            logger.error(f"Erro ao desconectar instância: {e}")
            return False


evolution_client = EvolutionClient()
