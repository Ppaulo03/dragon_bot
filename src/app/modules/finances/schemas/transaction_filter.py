from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class TransactionFilter(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1)
    q: Optional[str] = None
    account_id: Optional[int] = None
    type: Optional[str] = None
    manual: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("account_id", mode="before")
    @classmethod
    def parse_account_id(cls, v):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, v):
        if not v or not isinstance(v, str):
            return v
        try:
            return datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            return None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

    @property
    def start_timestamp(self) -> Optional[int]:
        return int(self.start_date.timestamp()) * 1000 if self.start_date else None

    @property
    def end_timestamp(self) -> Optional[int]:
        if self.end_date:
            return (
                int(self.end_date.replace(hour=23, minute=59, second=59).timestamp())
                * 1000
            )
        return None
