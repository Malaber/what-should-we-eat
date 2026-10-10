"""Persist recipe base portions; legacy recipes represent one batch."""
from alembic import op
import sqlalchemy as sa
revision = '20261009_03'
down_revision = '20261009_02'
branch_labels = depends_on = None

def upgrade():
    op.add_column('recipes', sa.Column('servings', sa.Float(), nullable=False, server_default='1'))

def downgrade():
    op.drop_column('recipes', 'servings')
