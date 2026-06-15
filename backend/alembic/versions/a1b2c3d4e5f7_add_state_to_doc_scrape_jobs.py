"""add_state_to_doc_scrape_jobs

Revision ID: a1b2c3d4e5f7
Revises: b2a1c3d4e5f6
Create Date: 2026-06-15 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "b2a1c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("doc_scrape_jobs", sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("doc_scrape_jobs", "state")
