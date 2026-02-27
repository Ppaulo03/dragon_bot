"""
Kernel Module - The core engine of Dragon Bot.
This file acts as a Facade, exposing essential interfaces and services
to the rest of the application.
"""

# 1. Core & Interfaces
from .core import (
    response_registry,
    MessageData,
    ChatClient,
    ChatResponse,
    MessageType,
    BaseModule,
)

# 2. Infrastructure Services (Instantiated)
from .infrastructure import storage_service, translate_service, external_api

# 3. Database Factory
from .infrastructure.database.postgres_client import PostgresClient

# 4. Utilities
from .utils import (
    setup_logging,
    calculate_phash,
    get_hash_from_b64,
    url_to_b64,
    setup_views,
    add_uuid_to_filename,
)

# 5. Global Config
from .config import settings

setup_logging()


__all__ = [
    # Core
    "response_registry",
    "MessageData",
    "ChatClient",
    "ChatResponse",
    "MessageType",
    "BaseModule",
    # Infrastructure
    "storage_service",
    "translate_service",
    "external_api",
    "PostgresClient",
    # Utilities
    "setup_logging",
    "calculate_phash",
    "get_hash_from_b64",
    "url_to_b64",
    "setup_views",
    "add_uuid_to_filename",
    # Config
    "settings",
]
