"""create ai interactions

Revision ID: 431e90271426
Revises: 13b40006c885
Create Date: 2026-07-29 23:06:16.419226

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '431e90271426'
down_revision: str | Sequence[str] | None = '13b40006c885'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ai_interaction_status = postgresql.ENUM(
    "proposed",
    "confirmed",
    "rejected",
    "expired",
    "clarification_requested",
    "answered",
    name="ai_interaction_status",
)


def upgrade() -> None:
    """Upgrade schema."""
    ai_interaction_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ai_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("interpreted_intent", postgresql.JSONB(), nullable=True),
        sa.Column("proposed_action", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "proposed",
                "confirmed",
                "rejected",
                "expired",
                "clarification_requested",
                "answered",
                name="ai_interaction_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "resulting_audit_log_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_log_entries.id"),
            nullable=True,
        ),
        sa.Column("response_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_ai_interactions_user_id_created_at", "ai_interactions", ["user_id", "created_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ai_interactions_user_id_created_at", table_name="ai_interactions")
    op.drop_table("ai_interactions")
    ai_interaction_status.drop(op.get_bind(), checkfirst=True)
