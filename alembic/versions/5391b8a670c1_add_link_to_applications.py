"""add_link_to_applications

Revision ID: 5391b8a670c1
Revises: b610c5984d3c
Create Date: 2025-05-09 14:31:34.028056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5391b8a670c1'
down_revision: Union[str, None] = 'b610c5984d3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add link column to applications table
    op.add_column('applications', sa.Column('link', sa.String(255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove link column from applications table
    op.drop_column('applications', 'link')
