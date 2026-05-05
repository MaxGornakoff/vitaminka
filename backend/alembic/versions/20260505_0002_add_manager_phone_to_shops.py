"""Add manager_phone to shops

Revision ID: 20260505_0002
Revises: 20260429_0001
Create Date: 2026-05-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260505_0002"
down_revision: Union[str, None] = "20260429_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shops", sa.Column("manager_phone", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("shops", "manager_phone")
