"""Optional recipe food icon; old recipes keep the default presentation."""
from alembic import op
import sqlalchemy as sa
revision = "20261103_01"
down_revision = "20261009_03"
branch_labels = depends_on = None

def upgrade():
    op.add_column("recipes", sa.Column("icon", sa.String(32), nullable=True))

def downgrade():
    op.drop_column("recipes", "icon")
