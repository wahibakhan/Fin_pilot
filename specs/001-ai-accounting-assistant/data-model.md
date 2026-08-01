# Phase 1 Data Model: FinPilot AI – AI-Powered Accounting & Finance Assistant

Derived from the Key Entities section of `spec.md` and the FR-034/FR-036/FR-037 validation & audit requirements. All tables use UUID primary keys, `created_at`/`updated_at` timestamps (UTC), and soft-delete (`deleted_at`, nullable) on the two transactional tables so that reports and audit history remain accurate for periods that included a since-deleted record — a "deleted" expense/income simply stops appearing in active views (ledger, dashboard, new reports) but is not physically erased, which is also what makes FR-030 (duplicate detection) and FR-037 (full audit trail) possible.

## Entity Relationship Overview

```text
users ──< expenses
users ──< income
users ──< audit_log_entries (actor_user_id)
users ──< ai_interactions

categories ──< expenses (category_id)

expenses ──< journal_entries (reference_type='expense')
income   ──< journal_entries (reference_type='income')

expenses ──< audit_log_entries (entity_type='expense')
income   ──< audit_log_entries (entity_type='income')

ai_interactions ──> audit_log_entries (resulting_audit_log_id, nullable)

refresh_tokens >── users
```

`ledger` from the original tech brief is implemented as a **read model** (a SQL view / service-layer query), not a physical table — it is the union of `expenses` and `income`, sorted by date. Persisting it as a separate table would create a second source of truth that manual edits, AI edits, and deletes would all have to keep in sync; a view has no sync risk. `journal_entries` remains a real table because it captures the double-entry (debit/credit) representation needed for Balance Sheet and Trial Balance, which is not simply "all transactions in one list."

## Tables

### users

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default gen_random_uuid() |
| full_name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(320) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| role | ENUM('business_owner','accountant','office_administrator') | NOT NULL |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: UNIQUE(email).

### categories

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL, UNIQUE |
| type | ENUM('expense','income','both') | NOT NULL, DEFAULT 'expense' |
| is_archived | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: UNIQUE(name). Archiving (rather than deleting) satisfies FR-036 — a category in use is archived, not dropped, so historical `expenses.category_id` references stay valid; archived categories are excluded from "create new expense" pickers but still render correctly on historical reports.

### expenses

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR(255) | NOT NULL |
| amount | NUMERIC(14,2) | NOT NULL, CHECK (amount > 0) |
| category_id | UUID | NOT NULL, FK → categories.id |
| date | DATE | NOT NULL |
| description | TEXT | NULL |
| created_by | UUID | NOT NULL, FK → users.id |
| created_via | ENUM('manual','ai') | NOT NULL, DEFAULT 'manual' |
| deleted_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: (date), (category_id), (created_by), partial index on `deleted_at IS NULL` for active-row scans.

### income

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| source | VARCHAR(255) | NOT NULL |
| amount | NUMERIC(14,2) | NOT NULL, CHECK (amount > 0) |
| date | DATE | NOT NULL |
| description | TEXT | NULL |
| created_by | UUID | NOT NULL, FK → users.id |
| created_via | ENUM('manual','ai') | NOT NULL, DEFAULT 'manual' |
| deleted_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: (date), (created_by), partial index on `deleted_at IS NULL`.

### journal_entries

Double-entry rows generated automatically whenever an expense or income row is created/edited/deleted (a delete posts a reversing entry rather than removing history). Backs Balance Sheet / Trial Balance / Cash Flow.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| reference_type | ENUM('expense','income') | NOT NULL |
| reference_id | UUID | NOT NULL |
| entry_type | ENUM('debit','credit') | NOT NULL |
| account | VARCHAR(100) | NOT NULL — e.g. "Cash", "Rent Expense", "Revenue" |
| amount | NUMERIC(14,2) | NOT NULL, CHECK (amount > 0) |
| entry_date | DATE | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: (reference_type, reference_id), (entry_date), (account).

### audit_log_entries

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| actor_type | ENUM('user','ai') | NOT NULL |
| actor_user_id | UUID | NOT NULL, FK → users.id (the human user; for AI actions, the user on whose behalf the assistant acted) |
| entity_type | ENUM('expense','income','category','user') | NOT NULL |
| entity_id | UUID | NOT NULL |
| action | ENUM('create','update','delete') | NOT NULL |
| before_state | JSONB | NULL |
| after_state | JSONB | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: (entity_type, entity_id), (created_at), (actor_user_id). Fulfils FR-029/FR-037; visibility restricted per FR-038 (Business Owner + Accountant only) at the service layer, not the schema layer.

### ai_interactions

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL, FK → users.id |
| user_message | TEXT | NOT NULL |
| interpreted_intent | JSONB | NULL — structured tool-call plan the agent produced |
| proposed_action | JSONB | NULL — the exact create/update/delete payload shown to the user for confirmation (FR-027) |
| status | ENUM('proposed','confirmed','rejected','expired','clarification_requested','answered') | NOT NULL |
| resulting_audit_log_id | UUID | NULL, FK → audit_log_entries.id |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: (user_id, created_at).

### refresh_tokens

Implementation detail supporting the JWT auth requirement (FR-001/FR-002); not a spec-level entity but required for logout-invalidation (User Story 1, Acceptance Scenario 3) to be real rather than client-side-only.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL, FK → users.id |
| token_hash | VARCHAR(255) | NOT NULL, UNIQUE |
| expires_at | TIMESTAMPTZ | NOT NULL |
| revoked_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Indexes: UNIQUE(token_hash), (user_id).

## Validation Rules (enforced in the service layer, mirrored in Pydantic v2 schemas)

- `amount > 0` on expenses, income, journal_entries (FR-012, FR-016).
- `date` must be a valid calendar date; report date ranges must have `end >= start` (FR-021).
- `category_id` on an expense must reference an existing, non-archived category at creation time (FR-012, FR-036).
- Role permission matrix (FR-003) enforced identically whether the mutation originates from a REST call or an AI tool call:
  - Office Administrator: create/edit expenses & income; no delete; no Balance Sheet/Trial Balance; no audit log access.
  - Accountant: full CRUD on expenses/income/categories; all reports; no audit log restriction beyond FR-038's Owner/Accountant rule.
  - Business Owner: full access, including audit log and user management.
- Every create/update/delete, regardless of origin, writes exactly one `audit_log_entries` row (FR-029, FR-037).
- Every AI-originated create/update/delete requires a corresponding `ai_interactions` row with `status = 'confirmed'` before the mutation is committed (FR-027).

## Derived/Read Models (no physical table)

- **Ledger**: `UNION ALL` of active (non-deleted) expenses and income, normalized to `(id, type, title_or_source, amount, category, date, description, created_by, created_via, created_at)`, paginated/sorted/filtered per FR-017/FR-018.
- **Dashboard summary**: aggregation query over the current period's expenses/income (FR-005–FR-008).
- **Reports** (FR-019): each of the seven report types is a parameterized aggregation query over `journal_entries` (Balance Sheet, Trial Balance, Cash Flow Summary) or over `expenses`/`income` directly (P&L, Monthly Expense, Income, Category-wise Expense); none require a dedicated table.
