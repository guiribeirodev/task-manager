"""create habits table

Revision ID: d4a8e21f9c10
Revises: c8f219b1a03e
Create Date: 2026-10-01 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a8e21f9c10'
down_revision: Union[str, Sequence[str], None] = 'c8f219b1a03e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

recurrence_period_enum = sa.Enum(
    'none', 'daily', 'weekly', 'monthly', name='recurrenceperiod'
)


def upgrade() -> None:
    """Upgrade schema."""
    recurrence_period_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'habits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), server_default='', nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column(
            'recurrence',
            recurrence_period_enum,
            server_default='daily',
            nullable=False,
        ),
        sa.Column('recurrence_days', sa.JSON(), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('habits')
