"""Expiring immutable recipe copies."""
from alembic import op
import sqlalchemy as sa
revision = '20261009_02'
down_revision = '20261009_01'
branch_labels = depends_on = None


def upgrade():
    op.create_table('recipe_shares',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('household_id', sa.Integer(), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('snapshot', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)))
    op.create_index('ix_recipe_shares_household_id', 'recipe_shares', ['household_id'])


def downgrade():
    op.drop_table('recipe_shares')
