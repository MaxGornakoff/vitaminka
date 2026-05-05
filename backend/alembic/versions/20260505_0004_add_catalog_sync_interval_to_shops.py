"""Add catalog_sync_interval_hours to shops

Revision ID: 20260505_0004
Revises: 20260505_0003
Create Date: 2026-05-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0004"
down_revision: Union[str, None] = "20260505_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shops",
        sa.Column("catalog_sync_interval_hours", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shops", "catalog_sync_interval_hours")
