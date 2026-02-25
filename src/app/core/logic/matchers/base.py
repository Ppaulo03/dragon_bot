from typing import Protocol, runtime_checkable
from app.core.interfaces import MessageData


@runtime_checkable
class Matcher(Protocol):
    async def is_match(self, msg: MessageData) -> bool: ...
