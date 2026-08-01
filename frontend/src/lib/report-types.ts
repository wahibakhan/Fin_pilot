import type { Action } from "@/lib/rbac";
import type { ReportType } from "@/lib/types";

export interface ReportTypeMeta {
  type: ReportType;
  label: string;
  description: string;
  requires?: Action;
}

export const REPORT_TYPES: ReportTypeMeta[] = [
  {
    type: "profit-and-loss",
    label: "Profit & Loss Statement",
    description: "Income vs. expenses over a period.",
  },
  {
    type: "balance-sheet",
    label: "Balance Sheet",
    description: "Assets, liabilities, and equity at a point in time.",
    requires: "reports:balance-sheet",
  },
  {
    type: "trial-balance",
    label: "Trial Balance",
    description: "Every ledger account's debit and credit totals.",
    requires: "reports:trial-balance",
  },
  {
    type: "cash-flow",
    label: "Cash Flow Summary",
    description: "Cash moving in and out over a period.",
  },
  {
    type: "monthly-expenses",
    label: "Monthly Expense Report",
    description: "Expenses broken down by month.",
  },
  { type: "income", label: "Income Report", description: "All recorded income for a period." },
  {
    type: "category-expenses",
    label: "Category-wise Expense Report",
    description: "Expenses grouped by category.",
  },
];

export function isReportType(value: string): value is ReportType {
  return REPORT_TYPES.some((r) => r.type === value);
}
