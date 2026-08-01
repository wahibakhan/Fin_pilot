"""create journal entries

Revision ID: 13b40006c885
Revises: 0c9511c8148f
Create Date: 2026-07-29 22:48:11.910134

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '13b40006c885'
down_revision: str | Sequence[str] | None = '0c9511c8148f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

journal_reference_type = postgresql.ENUM("expense", "income", name="journal_reference_type")
journal_entry_type = postgresql.ENUM("debit", "credit", name="journal_entry_type")


def upgrade() -> None:
    """Upgrade schema."""
    journal_reference_type.create(op.get_bind(), checkfirst=True)
    journal_entry_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "reference_type",
            postgresql.ENUM("expense", "income", name="journal_reference_type", create_type=False),
            nullable=False,
        ),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "entry_type",
            postgresql.ENUM("debit", "credit", name="journal_entry_type", create_type=False),
            nullable=False,
        ),
        sa.Column("account", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("amount > 0", name="ck_journal_entries_amount_positive"),
    )
    op.create_index(
        "ix_journal_entries_reference", "journal_entries", ["reference_type", "reference_id"]
    )
    op.create_index("ix_journal_entries_entry_date", "journal_entries", ["entry_date"])
    op.create_index("ix_journal_entries_account", "journal_entries", ["account"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_journal_entries_account", table_name="journal_entries")
    op.drop_index("ix_journal_entries_entry_date", table_name="journal_entries")
    op.drop_index("ix_journal_entries_reference", table_name="journal_entries")
    op.drop_table("journal_entries")

    journal_entry_type.drop(op.get_bind(), checkfirst=True)
    journal_reference_type.drop(op.get_bind(), checkfirst=True)
