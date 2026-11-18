"""Keep recipe sources private to the account that saved them."""
from alembic import op
import sqlalchemy as sa

revision = "20261118_02"
down_revision = "20261118_01"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "recipe_inbox_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(4), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "fingerprint", name="uq_recipe_inbox_owner_source"),
    )


def downgrade():
    op.drop_table("recipe_inbox_items")
