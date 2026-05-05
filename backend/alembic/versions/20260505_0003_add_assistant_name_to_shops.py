"""Add assistant_name to shops

Revision ID: 20260505_0003
Revises: 20260505_0002
Create Date: 2026-05-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260505_0003"
down_revision: Union[str, None] = "20260505_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shops",
        sa.Column("assistant_name", sa.String(length=255), nullable=True, server_default="Ассистент"),
    )


def downgrade() -> None:
    op.drop_column("shops", "assistant_name")
