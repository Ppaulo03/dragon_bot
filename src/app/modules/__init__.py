from app.kernel.core import module_registry

from .triggers import provider as triggers_provider


def setup_modules():
    module_registry.register(triggers_provider)
