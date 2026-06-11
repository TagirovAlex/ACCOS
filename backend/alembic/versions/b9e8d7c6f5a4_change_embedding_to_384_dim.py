"""change embedding vector dimension from 768 to 384

Revision ID: b9e8d7c6f5a4
Revises: fd9f90364766
Create Date: 2026-06-11 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b9e8d7c6f5a4"
down_revision: Union[str, None] = "fd9f90364766"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM knowledge_chunks")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(384)")


def downgrade() -> None:
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(768)")
