from typing import Dict, Callable, Any, Awaitable, Optional, List
from app.core.interfaces import MessageData, ChatResponse


ResponseCallable = Callable[[MessageData, str, Any], Awaitable[ChatResponse]]


class ResponseRegistry:
    def __init__(self):
        self._handlers: Dict[str, ResponseCallable] = {}

    def register(self, name: str):
        """Registra um método de resposta (ex: send_text, send_sticker)"""

        def wrapper(func: ResponseCallable):
            self._handlers[name] = func
            return func

        return wrapper

    def get_handler(self, name: str) -> Optional[ResponseCallable]:
        return self._handlers.get(name)

    def list_handlers(self) -> List[str]:
        return list(self._handlers.keys())


response_registry = ResponseRegistry()
