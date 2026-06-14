"""add web_fetch_permissions table

Revision ID: e5f4d3c2b1a0
Revises: c0d1e2f3a4b5
Create Date: 2026-06-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f4d3c2b1a0"
down_revision: Union[str, Sequence[str], None] = "c0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "web_fetch_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requests_per_hour", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("requests_per_day", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_chars", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("allowed_domains", sa.Text(), nullable=True),
        sa.Column("blocked_domains", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("web_fetch_permissions")
