"""initial_schema

Revision ID: 55e0906dd7af
Revises: None
Create Date: 2026-08-23 00:38:39.383052

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from db.models import Base

# revision identifiers, used by Alembic.
revision: str = '55e0906dd7af'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all ORM tables on target database bind."""
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    """Drop all ORM tables on target database bind."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
