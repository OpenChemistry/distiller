"""Remove log_files column

Revision ID: 6f6ae77c43f5
Revises: 7961c361c2de
Create Date: 2022-09-01 09:31:21.938103

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6f6ae77c43f5'
down_revision = '7961c361c2de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scans', 'log_files')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scans', sa.Column('log_files', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
