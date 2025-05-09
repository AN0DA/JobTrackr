"""add_subject_to_interactions

Revision ID: b610c5984d3c
Revises: abe249e110f8
Create Date: 2025-05-09 14:18:11.909276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b610c5984d3c'
down_revision: Union[str, None] = 'abe249e110f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('interactions', sa.Column('subject', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('interactions', 'subject')
