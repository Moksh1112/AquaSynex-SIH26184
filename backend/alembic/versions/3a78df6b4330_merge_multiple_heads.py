"""Merge multiple heads

Revision ID: 3a78df6b4330
Revises: a1b2c3d4e5f6, d085c41719ed
Create Date: 2026-09-15 14:50:12.470619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a78df6b4330'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'd085c41719ed')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
