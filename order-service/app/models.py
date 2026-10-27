
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    user_id: int
    item: str
    quantity: int
    amount: float
    status: str
    created_at: datetime


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(gt=0)
    item: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1000)
    amount: float = Field(ge=0)
    status: str = Field(default="pending", min_length=1, max_length=30)


def current_timestamp() -> datetime:
    return datetime.now(timezone.utc)
