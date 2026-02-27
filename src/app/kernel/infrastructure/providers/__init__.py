from fastapi import APIRouter
from app.kernel.infrastructure.network import BaseHttpClient
from .evolution import evolution_client, evolution_web_router
from typing import List

PROVIDERS: List[BaseHttpClient] = [evolution_client]
router = APIRouter()
router.include_router(evolution_web_router)
__all__ = ["evolution_client", "PROVIDERS", "router"]
