"""change habit_logs status to string

Revision ID: f2c81a94d012
Revises: dcc3046e5921
Create Date: 2026-10-02 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2c81a94d012'
down_revision: Union[str, Sequence[str], None] = 'dcc3046e5921'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'habit_logs'
                      AND column_name = 'status'
                      AND udt_name = 'habitlogstatus'
                ) THEN
                    ALTER TABLE habit_logs ALTER COLUMN status DROP DEFAULT;
                    ALTER TABLE habit_logs ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR;
                    ALTER TABLE habit_logs ALTER COLUMN status SET DEFAULT 'done';
                    DROP TYPE IF EXISTS habitlogstatus;
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
