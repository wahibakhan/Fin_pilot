"""create income

Revision ID: 0c9511c8148f
Revises: f6c28490af91
Create Date: 2026-07-29 22:22:45.788099

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0c9511c8148f'
down_revision: str | Sequence[str] | None = 'f6c28490af91'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # `created_via` enum already exists (created by the expenses migration) and
    # is shared between expenses and income.
    op.create_table(
        "income",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "created_via",
            postgresql.ENUM("manual", "ai", name="created_via", create_type=False),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("amount > 0", name="ck_income_amount_positive"),
    )
    op.create_index("ix_income_date", "income", ["date"])
    op.create_index("ix_income_created_by", "income", ["created_by"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_income_created_by", table_name="income")
    op.drop_index("ix_income_date", table_name="income")
    op.drop_table("income")
