"""Relax scan_id uniqueness constrant

Revision ID: a3b2fff032fd
Revises: f37b4be0b85b
Create Date: 2021-07-29 09:49:56.988136

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3b2fff032fd'
down_revision = 'f37b4be0b85b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_scans_scan_id', table_name='scans')
    op.create_index(op.f('ix_scans_scan_id'), 'scans', ['scan_id'], unique=False)
    op.create_unique_constraint('scan_id_created', 'scans', ['scan_id', 'created'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('scan_id_created', 'scans', type_='unique')
    op.drop_index(op.f('ix_scans_scan_id'), table_name='scans')
    op.create_index('ix_scans_scan_id', 'scans', ['scan_id'], unique=False)
    # ### end Alembic commands ###
