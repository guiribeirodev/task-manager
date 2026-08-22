"""add recurrence and due_date to todos

Revision ID: b7189c2f10d4
Revises: a9038c6f00c3
Create Date: 2026-08-04 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7189c2f10d4'
down_revision: Union[str, Sequence[str], None] = 'a9038c6f00c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

recurrence_period_enum = sa.Enum(
    'none', 'daily', 'weekly', 'monthly', name='recurrenceperiod'
)


def upgrade() -> None:
    """Upgrade schema."""
    recurrence_period_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'todos',
        sa.Column(
            'recurrence',
            recurrence_period_enum,
            server_default='none',
            nullable=False,
        ),
    )
    op.add_column('todos', sa.Column('due_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('todos', 'due_date')
    op.drop_column('todos', 'recurrence')
    recurrence_period_enum.drop(op.get_bind(), checkfirst=True)
