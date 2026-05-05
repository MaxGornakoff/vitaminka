"""Add catalog sync and index timestamps to shops

Revision ID: 20260505_0005
Revises: 20260505_0004
Create Date: 2026-05-05 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0005"
down_revision: Union[str, None] = "20260505_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shops", sa.Column("last_catalog_synced_at", sa.DateTime(), nullable=True))
    op.add_column("shops", sa.Column("last_catalog_indexed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("shops", "last_catalog_indexed_at")
    op.drop_column("shops", "last_catalog_synced_at")