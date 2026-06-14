"""add module_settings table

Revision ID: f1e2d3c4b5a6
Revises: 5c2755f18c3d
Create Date: 2026-06-14 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, Sequence[str], None] = "5c2755f18c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "module_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "module_name", "key", name="uq_module_setting_user_module_key"),
    )
    op.create_index(op.f("ix_module_settings_user_id"), "module_settings", ["user_id"])
    op.create_index(op.f("ix_module_settings_module_name"), "module_settings", ["module_name"])


def downgrade() -> None:
    op.drop_index(op.f("ix_module_settings_module_name"), table_name="module_settings")
    op.drop_index(op.f("ix_module_settings_user_id"), table_name="module_settings")
    op.drop_table("module_settings")
