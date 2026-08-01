export type CategoryType = "expense" | "income" | "both";

export interface Category {
  id: string;
  name: string;
  type: CategoryType;
  is_archived: boolean;
}

export type CreatedVia = "manual" | "ai";

export interface Expense {
  id: string;
  title: string;
  amount: string;
  category_id: string;
  date: string;
  description: string | null;
  created_by: string;
  created_via: CreatedVia;
  created_at: string;
  updated_at: string;
}

export interface ExpensePage {
  items: Expense[];
  total: number;
  page: number;
  page_size: number;
}

export interface Income {
  id: string;
  source: string;
  amount: string;
  date: string;
  description: string | null;
  created_by: string;
  created_via: CreatedVia;
  created_at: string;
  updated_at: string;
}

export interface IncomePage {
  items: Income[];
  total: number;
  page: number;
  page_size: number;
}

export interface LedgerEntry {
  id: string;
  type: "expense" | "income";
  label: string;
  amount: string;
  category: string | null;
  date: string;
  description: string | null;
  created_via: CreatedVia;
}

export interface LedgerPage {
  items: LedgerEntry[];
  total: number;
  page: number;
  page_size: number;
}

export type ReportType =
  | "profit-and-loss"
  | "balance-sheet"
  | "trial-balance"
  | "cash-flow"
  | "monthly-expenses"
  | "income"
  | "category-expenses";

export interface ProfitAndLossReport {
  date_from: string;
  date_to: string;
  total_income: string;
  total_expenses: string;
  net_profit: string;
}

export interface BalanceSheetReport {
  as_of: string;
  cash: string;
  total_assets: string;
  retained_earnings: string;
  total_equity: string;
}

export interface TrialBalanceReport {
  date_from: string;
  date_to: string;
  accounts: { account: string; total_debit: string; total_credit: string }[];
  total_debits: string;
  total_credits: string;
}

export interface CashFlowReport {
  date_from: string;
  date_to: string;
  cash_in: string;
  cash_out: string;
  net_cash_flow: string;
}

export interface MonthlyExpenseReport {
  date_from: string;
  date_to: string;
  months: { month: string; total: string }[];
  total_expenses: string;
}

export interface IncomeReport {
  date_from: string;
  date_to: string;
  months: { month: string; total: string }[];
  total_income: string;
}

export interface CategoryWiseExpenseReport {
  date_from: string;
  date_to: string;
  categories: { category: string; total: string }[];
  total_expenses: string;
}

export type AnyReport =
  | ProfitAndLossReport
  | BalanceSheetReport
  | TrialBalanceReport
  | CashFlowReport
  | MonthlyExpenseReport
  | IncomeReport
  | CategoryWiseExpenseReport;

export type AIInteractionStatus =
  | "proposed"
  | "confirmed"
  | "rejected"
  | "expired"
  | "clarification_requested"
  | "answered";

export interface AIChatResponse {
  interaction_id: string;
  conversation_id: string;
  status: AIInteractionStatus;
  message: string;
  proposed_action: Record<string, unknown> | null;
  data: Record<string, unknown> | null;
}

export interface DashboardSummary {
  date_from: string;
  date_to: string;
  total_income: string;
  total_expenses: string;
  net_profit: string;
  monthly_summary: { month: string; income: string; expenses: string }[];
  expense_categories: { category: string; total: string }[];
  recent_transactions: {
    id: string;
    type: "expense" | "income";
    label: string;
    amount: string;
    category: string | null;
    date: string;
  }[];
}

export type AuditActorType = "user" | "ai";
export type AuditEntityType = "expense" | "income" | "category" | "user";
export type AuditAction = "create" | "update" | "delete";

export interface AuditLogEntry {
  id: string;
  actor_type: AuditActorType;
  actor_user_id: string;
  entity_type: AuditEntityType;
  entity_id: string;
  action: AuditAction;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogPage {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}
