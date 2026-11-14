"""Stable ingredient ordering; legacy rows retain their id order."""
from alembic import op
import sqlalchemy as sa
revision = "20261103_02"
down_revision = "20261103_01"
branch_labels = depends_on = None

def upgrade():
    op.add_column("ingredients", sa.Column("position", sa.Integer(), nullable=False, server_default="0"))

def downgrade():
    op.drop_column("ingredients", "position")
