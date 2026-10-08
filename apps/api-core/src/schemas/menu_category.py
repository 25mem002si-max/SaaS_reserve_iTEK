
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MenuCategoryBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = None


class MenuCategoryCreate(MenuCategoryBase):
    restaurant_id: str


class MenuCategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    description: str | None = None


class MenuCategoryResponse(MenuCategoryBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str
    restaurant_id: str
    created_at: datetime
