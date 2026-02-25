from .evolution import evolution_client, evolution_router

PROVIDERS = {"evolution": evolution_client}
PROVIDERS_ROUTERS = [evolution_router]
__all__ = ["evolution_client", "PROVIDERS", "PROVIDERS_ROUTERS"]
