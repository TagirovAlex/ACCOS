"""add_doc_scrape_jobs_table

Revision ID: 5c2755f18c3d
Revises: e5f4d3c2b1a0
Create Date: 2026-06-14 09:13:56.588440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "5c2755f18c3d"
down_revision: Union[str, Sequence[str], None] = "e5f4d3c2b1a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doc_scrape_jobs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("site_url", sa.String(2048), nullable=False),
        sa.Column("site_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("pages_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_scraped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("doc_scrape_jobs")
