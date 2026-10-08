"""Add Onionary passkeys and single-use authorization state."""
from alembic import op
import sqlalchemy as sa

revision = "20261008_01"
down_revision = "20260402_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("passkeys",
        sa.Column("credential_id", sa.String(1024), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False))
    op.create_table("auth_flows",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table("auth_sessions")
    op.drop_table("auth_flows")
    op.drop_table("passkeys")
