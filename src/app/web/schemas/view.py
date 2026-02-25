from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from fastapi import UploadFile


class TriggerParams(BaseModel):
    pattern: Optional[str] = None
    hash: Optional[str] = None


class TriggerRule(BaseModel):
    id: str
    name: str
    type: str
    matcher: str = "always"
    chance: float = 1.0
    params: TriggerParams = Field(default_factory=TriggerParams)
    action: Optional[str] = None
    value: Optional[str] = None
    existing_files: List[str] = []
    new_files: List[UploadFile] = []
    trigger_upload: Optional[UploadFile] = None

    def dict_for_yaml(self) -> Dict[str, Any]:
        base = self.model_dump(
            exclude={"existing_files", "new_files", "trigger_upload"},
            exclude_none=True,
        )
        if self.existing_files:
            base["files"] = self.existing_files
        return base
