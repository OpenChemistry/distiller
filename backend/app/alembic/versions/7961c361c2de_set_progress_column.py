"""Set progress column

Revision ID: 7961c361c2de
Revises: a2e7fd87966b
Create Date: 2022-09-01 09:03:18.571627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7961c361c2de'
down_revision = 'a2e7fd87966b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE scans SET progress=log_files/0.72")
    op.alter_column('scans', 'progress', nullable=False)


def downgrade():
    op.alter_column('scans', 'progress', nullable=True)
    op.execute("UPDATE scans SET progress = NULL")
