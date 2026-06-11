"""change embedding vector dimension from 384 to 1024 (multilingual-e5-large)

Revision ID: c0d1e2f3a4b5
Revises: b9e8d7c6f5a4, a1b2c3d4e5f6
Create Date: 2026-06-11 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c0d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = ("b9e8d7c6f5a4", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM knowledge_chunks")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1024)")


def downgrade() -> None:
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(384)")
