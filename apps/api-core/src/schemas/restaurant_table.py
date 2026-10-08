from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.enums.table_status import TableStatus


class RestaurantTableCreate(BaseModel):
    table_number: int
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE


class RestaurantTableUpdate(BaseModel):
    table_number: int | None = None
    capacity: int | None = None
    status: TableStatus | None = None


class RestaurantTableResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    table_number: int
    capacity: int
    status: TableStatus

    model_config = ConfigDict(from_attributes=True)