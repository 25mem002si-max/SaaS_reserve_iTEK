from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "restaurants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    table_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "restaurant_tables.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    reservation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reservation_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    number_of_people: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )