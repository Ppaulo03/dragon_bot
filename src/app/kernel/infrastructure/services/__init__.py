from .storage import StorageService
from .translate import TranslateClient
from .api_client import ExternalApiClient

storage_service = StorageService()
translate_service = TranslateClient()
external_api = ExternalApiClient()

__all__ = ["storage_service", "translate_service", "external_api"]
