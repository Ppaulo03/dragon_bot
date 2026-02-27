import re
from .schemas import (
    TextMatchConfig,
    RegexMatchConfig,
    ImageMatchConfig,
    AlwaysMatchConfig,
)
from app.kernel import MessageData
from app.kernel.utils import get_hash_from_b64, url_to_b64


class TextMatcher:
    def __init__(self, config: dict):
        self.config = TextMatchConfig(**config)

    async def is_match(self, msg: MessageData) -> bool:
        body = msg.body if self.config.case_sensitive else msg.body.lower()
        pattern = (
            self.config.pattern
            if self.config.case_sensitive
            else self.config.pattern.lower()
        )
        return pattern in body


class RegexMatcher:
    def __init__(self, config: dict):
        self.config = RegexMatchConfig(**config)

    async def is_match(self, msg: MessageData) -> bool:
        return bool(re.search(self.config.pattern, msg.body, self.config.flags))


class ImageSimilarityMatcher:
    def __init__(self, config: dict):
        self.config = ImageMatchConfig(**config)

    async def is_match(self, msg: MessageData) -> bool:
        if not msg.is_img:
            return False

        if msg.cached_hash is None:
            if not msg.cached_b64:
                url = msg.body.split(" |&&| ")[0] if " |&&| " in msg.body else msg.body
                if url.startswith("http"):
                    msg.cached_b64 = await url_to_b64(url)
            if msg.cached_b64:
                msg.cached_hash = get_hash_from_b64(msg.cached_b64)
        if msg.cached_hash is None:
            return False

        return (msg.cached_hash - self.config.hash) <= self.config.threshold


class AlwaysMatcher:
    def __init__(self, config: dict):
        self.config = AlwaysMatchConfig(**config)

    async def is_match(self, msg: MessageData) -> bool:
        return True
