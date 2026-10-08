from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RestaurantCreate(BaseModel):
    name: str
    description: str | None = None
    address: str
    phone: str | None = None


class RestaurantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None


class RestaurantResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    address: str
    phone: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)