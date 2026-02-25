from .services.storage import StorageService
from .services.translate import TranslateClient
from .providers import evolution_client
from .webhooks import webhooks_router

storage = StorageService()
translate = TranslateClient()

__all__ = [
    "storage",
    "translate",
    "evolution_client",
    "webhooks_router",
]
