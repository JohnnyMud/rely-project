"""add cascade delete on calls patient fk

Revision ID: b7e4c2a91f05
Revises: 5c52530e7c76
Create Date: 2026-07-08 22:13:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7e4c2a91f05"
down_revision: Union[str, Sequence[str], None] = "5c52530e7c76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("calls_patient_id_fkey", "calls", type_="foreignkey")
    op.create_foreign_key(
        "calls_patient_id_fkey",
        "calls",
        "patients",
        ["patient_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("calls_patient_id_fkey", "calls", type_="foreignkey")
    op.create_foreign_key(
        "calls_patient_id_fkey",
        "calls",
        "patients",
        ["patient_id"],
        ["id"],
    )
