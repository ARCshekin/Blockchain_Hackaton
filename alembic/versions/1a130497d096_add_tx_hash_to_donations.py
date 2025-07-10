"""add_tx_hash_to_donations

Revision ID: 1a130497d096
Revises: d2cc0e28887f
Create Date: 2025-07-10 21:16:44.229564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a130497d096'
down_revision: Union[str, Sequence[str], None] = 'd2cc0e28887f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('donations', sa.Column('tx_hash', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('donations', 'tx_hash')
