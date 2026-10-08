from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field


class AvailableTableResponse(BaseModel):
    id: UUID
    table_number: int
    capacity: int


class AvailabilityResponse(BaseModel):
    restaurant_id: UUID
    reservation_date: date
    reservation_time: time
    number_of_people: int = Field(gt=0)
    available_tables: list[AvailableTableResponse]