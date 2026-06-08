"""add_seed_to_generation_records

Revision ID: 943ce26f1ef3
Revises: da4cb1f418e5
Create Date: 2026-06-08 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '943ce26f1ef3'
down_revision: Union[str, Sequence[str], None] = 'da4cb1f418e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('generation_records', sa.Column('seed', sa.BigInteger(), nullable=False, server_default=sa.text("'-1'")))


def downgrade() -> None:
    op.drop_column('generation_records', 'seed')
