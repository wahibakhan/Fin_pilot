import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReportView } from "@/components/tables/ReportView";
import type {
  BalanceSheetReport,
  CategoryWiseExpenseReport,
  ProfitAndLossReport,
  TrialBalanceReport,
} from "@/lib/types";

describe("ReportView", () => {
  it("renders Profit & Loss totals", () => {
    const report: ProfitAndLossReport = {
      date_from: "2026-07-01",
      date_to: "2026-07-31",
      total_income: "5000.00",
      total_expenses: "1000.00",
      net_profit: "4000.00",
    };

    render(<ReportView type="profit-and-loss" report={report} />);

    expect(screen.getByText("5,000.00")).toBeInTheDocument();
    expect(screen.getByText("1,000.00")).toBeInTheDocument();
    expect(screen.getByText("4,000.00")).toBeInTheDocument();
  });

  it("renders Balance Sheet as-of date and figures", () => {
    const report: BalanceSheetReport = {
      as_of: "2026-07-31",
      cash: "4000.00",
      total_assets: "4000.00",
      retained_earnings: "4000.00",
      total_equity: "4000.00",
    };

    render(<ReportView type="balance-sheet" report={report} />);

    expect(screen.getByText(/as of 2026-07-31/i)).toBeInTheDocument();
    expect(screen.getAllByText("4,000.00").length).toBeGreaterThan(0);
  });

  it("renders Trial Balance rows and totals, debits equal credits", () => {
    const report: TrialBalanceReport = {
      date_from: "2026-07-01",
      date_to: "2026-07-31",
      accounts: [
        { account: "Cash", total_debit: "5000.00", total_credit: "1000.00" },
        { account: "Expenses", total_debit: "1000.00", total_credit: "0.00" },
        { account: "Revenue", total_debit: "0.00", total_credit: "5000.00" },
      ],
      total_debits: "6000.00",
      total_credits: "6000.00",
    };

    render(<ReportView type="trial-balance" report={report} />);

    expect(screen.getByText("Cash")).toBeInTheDocument();
    expect(screen.getByText("Expenses")).toBeInTheDocument();
    expect(screen.getByText("Revenue")).toBeInTheDocument();
    expect(screen.getAllByText("6,000.00")).toHaveLength(2);
  });

  it("renders Category-wise Expense Report rows", () => {
    const report: CategoryWiseExpenseReport = {
      date_from: "2026-07-01",
      date_to: "2026-07-31",
      categories: [
        { category: "Rent", total: "1000.00" },
        { category: "Utilities", total: "200.00" },
      ],
      total_expenses: "1200.00",
    };

    render(<ReportView type="category-expenses" report={report} />);

    expect(screen.getByText("Rent")).toBeInTheDocument();
    expect(screen.getByText("Utilities")).toBeInTheDocument();
    expect(screen.getByText("1,200.00")).toBeInTheDocument();
  });
});
