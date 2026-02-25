import asyncio
import time
from typing import Any, Dict, Optional, TypeVar

import httpx
from loguru import logger
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T", bound="BaseHttpClient")


def is_retryable_exception(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 499, 502, 503, 504}
    return isinstance(
        exc, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
    )


class BaseHttpClient:
    _instances: Dict[Any, "BaseHttpClient"] = {}

    async def _get_client_lock(self):
        if not hasattr(self, "_client_lock_obj"):
            self._client_lock_obj = asyncio.Lock()
        return self._client_lock_obj

    def __init__(
        self,
        base_url: str,
        max_concurrent: int = 10,
        timeout: int = 15,
        headers: Optional[Dict[str, str]] = None,
        rate_limit_delay: float = 0.01,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
        http2: bool = True,
        retry_attempts: int = 3,
        retry_min_wait: int = 2,
        retry_max_wait: int = 10,
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self.http2 = http2
        self.http_client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()

        self._retrier = AsyncRetrying(
            retry=retry_if_exception(is_retryable_exception),
            wait=wait_exponential(multiplier=1, min=retry_min_wait, max=retry_max_wait),
            stop=stop_after_attempt(retry_attempts),
            reraise=True,
            before_sleep=self._log_retry_attempt,
        )

    async def _log_retry_attempt(self, retry_state):
        logger.warning(
            f"Tentativa {retry_state.attempt_number} falhou para {self.base_url}. "
            f"Aguardando {retry_state.upcoming_sleep}s antes de tentar novamente..."
        )

    async def close(self):
        if self.http_client and not self.http_client.is_closed:
            await self.http_client.aclose()

    async def get_http_client(self) -> httpx.AsyncClient:
        if self.http_client is None or self.http_client.is_closed:
            lock = await self._get_client_lock()
            async with lock:
                if self.http_client is None or self.http_client.is_closed:
                    self.http_client = httpx.AsyncClient(
                        headers=self.headers,
                        timeout=self.timeout,
                        limits=self.limits,
                        http2=self.http2,
                    )
        return self.http_client

    async def _do_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        client = await self.get_http_client()
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()

        try:
            return response.json()
        except (httpx.DecodingError, ValueError):
            return {"status": "success", "text": response.text}

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        elapsed = time.monotonic() - self._last_request_time
        if (delay := self.rate_limit_delay - elapsed) > 0:
            await asyncio.sleep(delay)

        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            if kwargs.get("json") is None:
                kwargs.pop("json", None)

            async with self._semaphore:
                res = await self._retrier(self._do_request, method, url, **kwargs)
                self._last_request_time = time.monotonic()
                return res

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de Status HTTP: {e.response.status_code} em {url}")
            raise e
        except Exception as e:
            logger.exception(f"Erro inesperado na requisição para {url}")
            raise e

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return await self.request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, json: Optional[Dict] = None, data: Any = None
    ) -> Dict[str, Any]:
        return await self.request("POST", endpoint, json=json, data=data)

    async def delete(
        self, endpoint: str, json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        return await self.request("DELETE", endpoint, json=json)
