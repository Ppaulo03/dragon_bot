from .base import Matcher
from typing import Dict
from .implementations import (
    TextMatcher,
    RegexMatcher,
    ImageSimilarityMatcher,
    AlwaysMatcher,
)

MATCHER_REGISTRY: Dict[str, type[Matcher]] = {
    "text": TextMatcher,
    "regex": RegexMatcher,
    "image_similarity": ImageSimilarityMatcher,
    "always": AlwaysMatcher,
}

__all__ = ["Matcher", "MATCHER_REGISTRY"]
