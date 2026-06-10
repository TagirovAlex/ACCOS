"""change embedding vector dimension from 1536 to 768

Revision ID: ac5c6f89d2e4
Revises: 1c7d9b7e245d
Create Date: 2026-06-10 15:19:50.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "ac5c6f89d2e4"
down_revision: Union[str, None] = "1c7d9b7e245d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(768)")


def downgrade() -> None:
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1536)")
