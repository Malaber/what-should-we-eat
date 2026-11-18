"""Store the tools needed to cook each recipe."""
from alembic import op
import sqlalchemy as sa

revision = "20261118_01"
down_revision = "20261103_03"
branch_labels = depends_on = None


def upgrade():
    op.add_column("recipes", sa.Column("equipment", sa.JSON(), server_default="[]", nullable=False))


def downgrade():
    op.drop_column("recipes", "equipment")
