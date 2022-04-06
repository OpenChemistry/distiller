"""Add scan metadata

Revision ID: bdfc80022da8
Revises: da63207a94fc
Create Date: 2022-03-21 15:15:48.175718

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bdfc80022da8'
down_revision = 'da63207a94fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scans', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scans', 'metadata')
    # ### end Alembic commands ###