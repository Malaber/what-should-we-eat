"""Named sections for ingredient lists and instructions."""
from alembic import op
import sqlalchemy as sa
revision = "20261103_03"
down_revision = "20261103_02"
branch_labels = depends_on = None

def upgrade():
    for table in ("ingredients", "instruction_steps"):
        op.add_column(table, sa.Column("group_name", sa.String(100), nullable=True))

def downgrade():
    for table in ("ingredients", "instruction_steps"):
        op.drop_column(table, "group_name")
