"""make todo user_id nullable

Revision ID: 7b2d4c1e9a0f
Revises: 1f68ad92497c
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2d4c1e9a0f'
down_revision: Union[str, Sequence[str], None] = '1f68ad92497c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'todos',
        'user_id',
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'todos',
        'user_id',
        existing_type=sa.Integer(),
        nullable=False,
    )