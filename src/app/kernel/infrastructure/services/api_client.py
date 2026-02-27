from typing import Any, Optional
from ..network import BaseHttpClient


class ExternalApiClient(BaseHttpClient):
    def __init__(self):
        super().__init__(
            base_url="",
            max_concurrent=15,
            timeout=15,
            retry_attempts=2,
        )

    async def fetch(self, url: str) -> Optional[Any]:
        """
        Método especializado para buscar de URLs completas de APIs externas.
        """
        try:
            return await self.request("GET", url)
        except Exception:
            return None
