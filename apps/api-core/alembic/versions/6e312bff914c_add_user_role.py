"""add user role

Revision ID: 6e312bff914c
Revises: 219ea1900740
Create Date: 2026-09-01 15:10:51.562077

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6e312bff914c"
down_revision: Union[str, Sequence[str], None] = "219ea1900740"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajouter la colonne role avec "client" comme
    # valeur par défaut pour les utilisateurs existants.
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="client",
        ),
    )

    # Retirer la valeur par défaut côté PostgreSQL
    # après avoir initialisé les utilisateurs existants.
    op.alter_column(
        "users",
        "role",
        server_default=None,
    )


def downgrade() -> None:
    # Supprimer la colonne role en cas de retour arrière.
    op.drop_column(
        "users",
        "role",
    )