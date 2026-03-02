from app.kernel.core import module_registry

# from .triggers import provider as triggers_provider
from .finances import provider as finance_provider


from app.kernel.core.registry import module_registry


def setup_modules():

    # module_registry.register(triggers_provider)
    module_registry.register(finance_provider)
