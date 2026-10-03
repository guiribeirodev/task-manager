"""create habit_logs table

Revision ID: dcc3046e5921
Revises: d4a8e21f9c10
Create Date: 2026-10-01 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcc3046e5921'
down_revision: Union[str, Sequence[str], None] = 'd4a8e21f9c10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'habit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column(
            'status',
            sa.String(),
            server_default='done',
            nullable=False,
        ),
        sa.Column('notes', sa.String(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ['habit_id'], ['habits.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('habit_id', 'date', name='uq_habit_log_habit_date'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('habit_logs')
