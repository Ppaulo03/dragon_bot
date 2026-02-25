from loguru import logger
from app.infrastructure.network import BaseHttpClient
from app.config import settings


class TranslateClient(BaseHttpClient):

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self.active = bool(settings.TRANSLATE_URL)
        if not self.active:
            logger.warning(
                "TranslateClient: TRANSLATE_URL não configurada. O serviço retornará o texto original."
            )
            self._initialized = True
            return

        super().__init__(
            base_url=settings.TRANSLATE_URL,
            timeout=settings.TRANSLATE_TIMEOUT,
            max_concurrent=5,
        )

        if settings.TRANSLATE_API_KEY:
            self.headers.update(
                {"Authorization": f"Bearer {settings.TRANSLATE_API_KEY}"}
            )

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
        format: str = "text",
    ) -> str:
        if not self.active or not text:
            return text

        payload = {
            "q": text,
            "target": target_lang,
            "source": source_lang,
            "format": format,
        }

        try:
            response = await self.post("translate", json=payload)
            if isinstance(response, dict) and "translatedText" in response:
                return response["translatedText"]
            return text

        except Exception as e:
            logger.exception(f"Falha na tradução de '{text[:20]}...': {e}")
            return text
