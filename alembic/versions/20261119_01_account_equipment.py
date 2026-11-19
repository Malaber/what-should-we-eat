"""Sync equipment ownership across clients of an account."""
from alembic import op
import sqlalchemy as sa

revision = "20261119_01"
down_revision = "20261118_02"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "account_equipment",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("name", sa.String(640), primary_key=True),
        sa.Column("owned", sa.Boolean(), nullable=False),
    )


def downgrade():
    op.drop_table("account_equipment")
