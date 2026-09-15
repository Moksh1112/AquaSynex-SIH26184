"""Add police_stations table

Revision ID: a1b2c3d4e5f6
Revises: fcb3665d399c
Create Date: 2026-09-15 14:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fcb3665d399c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add police_stations table for Response Intelligence enrichment."""
    op.create_table(
        'police_stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('station_id', sa.String(), nullable=False),
        sa.Column('station_name', sa.String(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('jurisdiction_code', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_police_stations_id'), 'police_stations', ['id'], unique=False)
    op.create_index(op.f('ix_police_stations_station_id'), 'police_stations', ['station_id'], unique=True)


def downgrade() -> None:
    """Remove police_stations table."""
    op.drop_index(op.f('ix_police_stations_station_id'), table_name='police_stations')
    op.drop_index(op.f('ix_police_stations_id'), table_name='police_stations')
    op.drop_table('police_stations')
