from .module_registry import ModuleRegistry
from .response_registry import ResponseRegistry

module_registry = ModuleRegistry()
response_registry = ResponseRegistry()
__all__ = ["module_registry", "response_registry"]
