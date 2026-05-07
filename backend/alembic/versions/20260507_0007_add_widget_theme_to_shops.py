"""add widget theme fields to shops

Revision ID: 20260507_0007
Revises: 20260505_0006
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa

revision = "20260507_0007"
down_revision = "20260505_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("shops", sa.Column("widget_color_primary", sa.String(30), nullable=True))
    op.add_column("shops", sa.Column("widget_color_secondary", sa.String(30), nullable=True))
    op.add_column("shops", sa.Column("widget_color_bg", sa.String(30), nullable=True))
    op.add_column("shops", sa.Column("widget_border_radius", sa.Integer, nullable=True))
    op.add_column("shops", sa.Column("widget_custom_css", sa.Text, nullable=True))


def downgrade():
    op.drop_column("shops", "widget_custom_css")
    op.drop_column("shops", "widget_border_radius")
    op.drop_column("shops", "widget_color_bg")
    op.drop_column("shops", "widget_color_secondary")
    op.drop_column("shops", "widget_color_primary")
