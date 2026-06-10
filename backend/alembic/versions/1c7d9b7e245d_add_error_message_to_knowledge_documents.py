"""add error_message to knowledge_documents

Revision ID: 1c7d9b7e245d
Revises: 15a0dfe29b8e
Create Date: 2026-06-10 17:05:43.805807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c7d9b7e245d'
down_revision: Union[str, Sequence[str], None] = '15a0dfe29b8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_documents', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_documents', 'error_message')
