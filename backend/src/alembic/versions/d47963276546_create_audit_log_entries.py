"""create audit log entries

Revision ID: d47963276546
Revises: fc318bcad0c4
Create Date: 2026-07-29 21:35:55.564831

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd47963276546'
down_revision: str | Sequence[str] | None = 'fc318bcad0c4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

actor_type = postgresql.ENUM("user", "ai", name="actor_type")
audit_entity_type = postgresql.ENUM("expense", "income", "category", "user", name="audit_entity_type")
audit_action = postgresql.ENUM("create", "update", "delete", name="audit_action")


def upgrade() -> None:
    """Upgrade schema."""
    actor_type.create(op.get_bind(), checkfirst=True)
    audit_entity_type.create(op.get_bind(), checkfirst=True)
    audit_action.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "audit_log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_type",
            postgresql.ENUM("user", "ai", name="actor_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "entity_type",
            postgresql.ENUM(
                "expense", "income", "category", "user", name="audit_entity_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "action",
            postgresql.ENUM("create", "update", "delete", name="audit_action", create_type=False),
            nullable=False,
        ),
        sa.Column("before_state", postgresql.JSONB(), nullable=True),
        sa.Column("after_state", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_audit_log_entries_actor_user_id", "audit_log_entries", ["actor_user_id"])
    op.create_index("ix_audit_log_entries_created_at", "audit_log_entries", ["created_at"])
    op.create_index(
        "ix_audit_log_entries_entity_type_entity_id",
        "audit_log_entries",
        ["entity_type", "entity_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_audit_log_entries_entity_type_entity_id", table_name="audit_log_entries")
    op.drop_index("ix_audit_log_entries_created_at", table_name="audit_log_entries")
    op.drop_index("ix_audit_log_entries_actor_user_id", table_name="audit_log_entries")
    op.drop_table("audit_log_entries")

    audit_action.drop(op.get_bind(), checkfirst=True)
    audit_entity_type.drop(op.get_bind(), checkfirst=True)
    actor_type.drop(op.get_bind(), checkfirst=True)
