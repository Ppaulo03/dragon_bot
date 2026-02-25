import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any
from imagehash import ImageHash, hex_to_hash


class TextMatchConfig(BaseModel):
    pattern: str
    case_sensitive: bool = False


class RegexMatchConfig(BaseModel):
    pattern: str
    flags: int = re.IGNORECASE


class ImageMatchConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hash: ImageHash
    threshold: int = Field(default=5, ge=0, le=64)

    @field_validator("hash", mode="before")
    @classmethod
    def parse_hash(cls, v: Any) -> ImageHash:
        if isinstance(v, str):
            return hex_to_hash(v)
        return v


class AlwaysMatchConfig(BaseModel):
    pass
