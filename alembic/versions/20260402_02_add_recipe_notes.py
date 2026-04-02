"""add recipe notes

Revision ID: 20260402_02
Revises: 20260402_01
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_02"
down_revision = "20260402_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("recipes")}
    if "notes" not in columns:
        op.add_column("recipes", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("recipes")}
    if "notes" in columns:
        op.drop_column("recipes", "notes")
