from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    reservation_id: UUID
    amount: Decimal
    currency: str = "USD"
    payment_method: str | None = None


class PaymentStatusUpdate(BaseModel):
    status: str
    transaction_id: str | None = None


class PaymentResponse(BaseModel):
    id: UUID
    reservation_id: UUID
    amount: Decimal
    currency: str
    status: str
    payment_method: str | None
    transaction_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)