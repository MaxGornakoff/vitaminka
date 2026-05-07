"""add widget_currency_symbol to shops

Revision ID: 20260507_0008
Revises: 20260507_0007
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa

revision = "20260507_0008"
down_revision = "20260507_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("shops", sa.Column("widget_currency_symbol", sa.String(20), nullable=True))


def downgrade():
    op.drop_column("shops", "widget_currency_symbol")
