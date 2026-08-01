import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatCards } from "@/components/charts/StatCards";
import { MonthlySummary } from "@/components/charts/MonthlySummary";
import { RecentTransactions } from "@/components/tables/RecentTransactions";

describe("StatCards", () => {
  it("renders formatted totals", () => {
    render(<StatCards totalIncome="5000.00" totalExpenses="1000.00" netProfit="4000.00" />);

    expect(screen.getByText("Total Income")).toBeInTheDocument();
    expect(screen.getByText("5,000.00")).toBeInTheDocument();
    expect(screen.getByText("1,000.00")).toBeInTheDocument();
    expect(screen.getByText("4,000.00")).toBeInTheDocument();
  });
});

describe("MonthlySummary", () => {
  it("computes net per month from income and expenses", () => {
    render(
      <MonthlySummary
        months={[{ month: "2026-07", income: "5000.00", expenses: "1000.00" }]}
      />
    );

    expect(screen.getByText("2026-07")).toBeInTheDocument();
    expect(screen.getByText("4,000.00")).toBeInTheDocument();
  });

  it("shows an empty state with no months", () => {
    render(<MonthlySummary months={[]} />);
    expect(screen.getByText(/no data for this period/i)).toBeInTheDocument();
  });
});

describe("RecentTransactions", () => {
  it("renders both expense and income rows", () => {
    render(
      <RecentTransactions
        transactions={[
          { id: "1", type: "expense", label: "Office Rent", amount: "1000.00", category: "Rent", date: "2026-07-01" },
          { id: "2", type: "income", label: "Consulting Fee", amount: "5000.00", category: null, date: "2026-07-02" },
        ]}
      />
    );

    expect(screen.getByText("Office Rent")).toBeInTheDocument();
    expect(screen.getByText("Consulting Fee")).toBeInTheDocument();
    expect(screen.getByText("Expense")).toBeInTheDocument();
    expect(screen.getByText("Income")).toBeInTheDocument();
  });

  it("shows an empty state with no transactions", () => {
    render(<RecentTransactions transactions={[]} />);
    expect(screen.getByText(/no transactions yet/i)).toBeInTheDocument();
  });
});
