"""add file_hash to knowledge_documents

Revision ID: e7f3a2b1c9d0
Revises: ac5c6f89d2e4
Create Date: 2026-06-11 08:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f3a2b1c9d0'
down_revision: Union[str, Sequence[str], None] = 'ac5c6f89d2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_documents', sa.Column('file_hash', sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_documents', 'file_hash')
