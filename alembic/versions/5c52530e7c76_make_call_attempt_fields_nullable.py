"""make call attempt fields nullable

Revision ID: 5c52530e7c76
Revises: a17215be68c2
Create Date: 2026-07-06 15:14:49.158349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c52530e7c76'
down_revision: Union[str, Sequence[str], None] = 'a17215be68c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("calls", "retell_call_id", existing_type=sa.String(), nullable=True)
    op.alter_column("calls", "started_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("calls", "ended_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("calls", "call_duration", existing_type=sa.Integer(), nullable=True)
    op.alter_column("calls", "successful", existing_type=sa.Boolean(), nullable=True)
    op.alter_column("calls", "recording_url", existing_type=sa.String(), nullable=True)
    op.alter_column("calls", "summary", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("calls", "summary", existing_type=sa.Text(), nullable=False)
    op.alter_column("calls", "recording_url", existing_type=sa.String(), nullable=False)
    op.alter_column("calls", "successful", existing_type=sa.Boolean(), nullable=False)
    op.alter_column("calls", "call_duration", existing_type=sa.Integer(), nullable=False)
    op.alter_column("calls", "ended_at", existing_type=sa.DateTime(), nullable=False)
    op.alter_column("calls", "started_at", existing_type=sa.DateTime(), nullable=False)
    op.alter_column("calls", "retell_call_id", existing_type=sa.String(), nullable=False)
