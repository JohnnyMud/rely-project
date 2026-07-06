"""rename calls recording url column

Revision ID: 258d0bfd479b
Revises: cd4a0bd328db
Create Date: 2026-07-06 13:53:39.370868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '258d0bfd479b'
down_revision: Union[str, Sequence[str], None] = 'cd4a0bd328db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "calls",
        "recordeding_url",
        new_column_name="recording_url",
        existing_type=sa.String(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "calls",
        "recording_url",
        new_column_name="recordeding_url",
        existing_type=sa.String(),
        existing_nullable=False,
    )
