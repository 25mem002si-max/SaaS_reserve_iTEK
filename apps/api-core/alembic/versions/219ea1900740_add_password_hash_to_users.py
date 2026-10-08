"""add password hash to users

Revision ID: 219ea1900740
Revises: cc6631510b5c
Create Date: 2026-08-27 07:29:39.317614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "219ea1900740"
down_revision: Union[str, Sequence[str], None] = "cc6631510b5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True
        )
    )

    op.execute(
        "UPDATE users SET password_hash = 'TEMP_PASSWORD_HASH'"
    )

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False
    )


def downgrade() -> None:
    op.drop_column("users", "password_hash")