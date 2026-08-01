"""create expenses

Revision ID: f6c28490af91
Revises: d47963276546
Create Date: 2026-07-29 21:37:15.853250

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6c28490af91'
down_revision: str | Sequence[str] | None = 'd47963276546'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

created_via = postgresql.ENUM("manual", "ai", name="created_via")


def upgrade() -> None:
    """Upgrade schema."""
    created_via.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=False
        ),
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
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
    )
    op.create_index("ix_expenses_category_id", "expenses", ["category_id"])
    op.create_index("ix_expenses_date", "expenses", ["date"])
    op.create_index("ix_expenses_created_by", "expenses", ["created_by"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_expenses_created_by", table_name="expenses")
    op.drop_index("ix_expenses_date", table_name="expenses")
    op.drop_index("ix_expenses_category_id", table_name="expenses")
    op.drop_table("expenses")
    created_via.drop(op.get_bind(), checkfirst=True)
