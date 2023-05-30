"""Make scan_id nullable

Revision ID: b78a681849ce
Revises: 6463a9e6e760
Create Date: 2023-05-30 15:52:49.434774

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b78a681849ce"
down_revision = "6463a9e6e760"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("jobs", "scan_id", existing_type=sa.Integer(), nullable=True)


def downgrade():
    op.alter_column("jobs", "scan_id", existing_type=sa.Integer(), nullable=False)
