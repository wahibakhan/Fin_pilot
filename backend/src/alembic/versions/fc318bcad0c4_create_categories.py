"""create categories

Revision ID: fc318bcad0c4
Revises: 057301e15c38
Create Date: 2026-07-29 21:34:45.350511

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fc318bcad0c4'
down_revision: str | Sequence[str] | None = '057301e15c38'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

category_type = postgresql.ENUM("expense", "income", "both", name="category_type")


def upgrade() -> None:
    """Upgrade schema."""
    category_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("expense", "income", "both", name="category_type", create_type=False),
            nullable=False,
            server_default="expense",
        ),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
    category_type.drop(op.get_bind(), checkfirst=True)
