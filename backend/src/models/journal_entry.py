import uuid
from datetime import date as date_
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class JournalEntryType(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class JournalReferenceType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class JournalEntry(Base):
    """Double-entry postings backing Balance Sheet / Trial Balance / Cash Flow.

    No FK on (reference_type, reference_id) — it's a polymorphic reference to
    either `expenses` or `income`, matching data-model.md.
    """

    __tablename__ = "journal_entries"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_journal_entries_amount_positive"),
        Index("ix_journal_entries_reference", "reference_type", "reference_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference_type: Mapped[JournalReferenceType] = mapped_column(
        PgEnum(
            JournalReferenceType,
            name="journal_reference_type",
            create_type=True,
            inherit_schema=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    reference_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    entry_type: Mapped[JournalEntryType] = mapped_column(
        PgEnum(
            JournalEntryType,
            name="journal_entry_type",
            create_type=True,
            inherit_schema=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    account: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    entry_date: Mapped[date_] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
