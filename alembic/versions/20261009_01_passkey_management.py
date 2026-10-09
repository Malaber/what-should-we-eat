"""Passkey labels, usage metadata and auditable one-time add links."""
from alembic import op
import sqlalchemy as sa
revision = "20261009_01"
down_revision = "20261008_01"
branch_labels = depends_on = None


def upgrade():
    op.add_column("passkeys", sa.Column("name", sa.String(120), nullable=False, server_default="Passkey"))
    op.add_column("passkeys", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("passkeys", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("passkey_add_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_table("passkey_add_links")
    op.drop_column("passkeys", "last_used_at")
    op.drop_column("passkeys", "created_at")
    op.drop_column("passkeys", "name")
