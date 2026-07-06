"""convert ids to uuid with defaults

Revision ID: a17215be68c2
Revises: 258d0bfd479b
Create Date: 2026-07-06 15:03:20.908282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a17215be68c2'
down_revision: Union[str, Sequence[str], None] = '258d0bfd479b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.alter_column(
        "patients",
        "id",
        existing_type=sa.String(),
        server_default=sa.text("gen_random_uuid()::text"),
        existing_nullable=False,
    )
    op.alter_column(
        "calls",
        "call_attempt_id",
        existing_type=sa.String(),
        server_default=sa.text("gen_random_uuid()::text"),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "calls",
        "call_attempt_id",
        existing_type=sa.String(),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "patients",
        "id",
        existing_type=sa.String(),
        server_default=None,
        existing_nullable=False,
    )
