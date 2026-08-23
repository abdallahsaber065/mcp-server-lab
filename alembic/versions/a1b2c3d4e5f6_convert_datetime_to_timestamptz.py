"""convert datetime columns to timestamptz

Revision ID: a1b2c3d4e5f6
Revises: 55e0906dd7af
Create Date: 2026-08-25 11:45:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '55e0906dd7af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATETIME_COLUMNS = [
    ("agent_tool_bindings", "updated_at"),
    ("chat_sessions", "created_at"),
    ("chat_sessions", "updated_at"),
    ("episodic_memory", "timestamp"),
    ("graph_checkpoints", "created_at"),
    ("graph_failure_tickets", "created_at"),
    ("graph_failure_tickets", "resolved_at"),
    ("hitl_tasks", "created_at"),
    ("hitl_tasks", "resolved_at"),
    ("properties", "created_at"),
    ("rag_document_embeddings", "created_at"),
    ("rag_documents", "created_at"),
    ("tenants", "created_at"),
    ("chat_messages", "created_at"),
    ("units", "created_at"),
    ("lease_applications", "created_at"),
    ("leases", "renewal_requested_at"),
    ("leases", "created_at"),
    ("maintenance_requests", "submitted_at"),
    ("maintenance_requests", "resolved_at"),
    ("tour_bookings", "created_at"),
    ("payments", "payment_date"),
    ("payments", "created_at"),
]


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Check table existence before altering
        for table, column in DATETIME_COLUMNS:
            res = bind.execute(
                sa.text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = :tbl AND column_name = :col"
                ),
                {"tbl": table, "col": column},
            ).fetchone()
            if res:
                op.execute(
                    f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMPTZ USING {column} AT TIME ZONE 'UTC'"
                )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        for table, column in DATETIME_COLUMNS:
            res = bind.execute(
                sa.text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = :tbl AND column_name = :col"
                ),
                {"tbl": table, "col": column},
            ).fetchone()
            if res:
                op.execute(
                    f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITHOUT TIME ZONE USING {column} AT TIME ZONE 'UTC'"
                )
