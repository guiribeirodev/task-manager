"""add recurrence_days to todos

Revision ID: c8f219b1a03e
Revises: b7189c2f10d4
Create Date: 2026-08-22 22:23:51.182711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f219b1a03e'
down_revision: Union[str, Sequence[str], None] = 'b7189c2f10d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('todos', sa.Column('recurrence_days', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('todos', 'recurrence_days')

