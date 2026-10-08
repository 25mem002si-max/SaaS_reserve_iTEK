from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReservationCreate(BaseModel):
    restaurant_id: UUID
    table_id: UUID
    reservation_date: date
    reservation_time: time
    number_of_people: int


class ReservationUpdate(BaseModel):
    reservation_date: date | None = None
    reservation_time: time | None = None
    number_of_people: int | None = None


class ReservationStatusUpdate(BaseModel):
    status: str


class ReservationResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    table_id: UUID
    user_id: UUID
    reservation_date: date
    reservation_time: time
    number_of_people: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)