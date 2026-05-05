"""add vendor to products

Revision ID: 20260505_0006
Revises: 20260505_0005
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260505_0006"
down_revision = "20260505_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("products", sa.Column("vendor", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("products", "vendor")
