"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ReportBarChart } from "@/components/charts/ReportCharts";
import type {
  AnyReport,
  BalanceSheetReport,
  CashFlowReport,
  CategoryWiseExpenseReport,
  IncomeReport,
  MonthlyExpenseReport,
  ProfitAndLossReport,
  ReportType,
  TrialBalanceReport,
} from "@/lib/types";

function money(value: string): string {
  return Number(value).toLocaleString(undefined, { minimumFractionDigits: 2 });
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent className="text-2xl font-semibold">{money(value)}</CardContent>
    </Card>
  );
}

interface ReportViewProps {
  type: ReportType;
  report: AnyReport;
}

export function ReportView({ type, report }: ReportViewProps) {
  switch (type) {
    case "profit-and-loss": {
      const r = report as ProfitAndLossReport;
      return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Total Income" value={r.total_income} />
          <StatCard label="Total Expenses" value={r.total_expenses} />
          <StatCard label="Net Profit" value={r.net_profit} />
        </div>
      );
    }

    case "balance-sheet": {
      const r = report as BalanceSheetReport;
      return (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">As of {r.as_of}</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <StatCard label="Cash" value={r.cash} />
            <StatCard label="Total Assets" value={r.total_assets} />
            <StatCard label="Retained Earnings" value={r.retained_earnings} />
            <StatCard label="Total Equity" value={r.total_equity} />
          </div>
        </div>
      );
    }

    case "trial-balance": {
      const r = report as TrialBalanceReport;
      return (
        <div className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead className="text-right">Total Debit</TableHead>
                <TableHead className="text-right">Total Credit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {r.accounts.map((a) => (
                <TableRow key={a.account}>
                  <TableCell>{a.account}</TableCell>
                  <TableCell className="text-right">{money(a.total_debit)}</TableCell>
                  <TableCell className="text-right">{money(a.total_credit)}</TableCell>
                </TableRow>
              ))}
              <TableRow className="font-semibold">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">{money(r.total_debits)}</TableCell>
                <TableCell className="text-right">{money(r.total_credits)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      );
    }

    case "cash-flow": {
      const r = report as CashFlowReport;
      return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Cash In" value={r.cash_in} />
          <StatCard label="Cash Out" value={r.cash_out} />
          <StatCard label="Net Cash Flow" value={r.net_cash_flow} />
        </div>
      );
    }

    case "monthly-expenses": {
      const r = report as MonthlyExpenseReport;
      return (
        <div className="space-y-4">
          <StatCard label="Total Expenses" value={r.total_expenses} />
          <ReportBarChart
            data={r.months.map((m) => ({ label: m.month, value: Number(m.total) }))}
          />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Month</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {r.months.map((m) => (
                <TableRow key={m.month}>
                  <TableCell>{m.month}</TableCell>
                  <TableCell className="text-right">{money(m.total)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      );
    }

    case "income": {
      const r = report as IncomeReport;
      return (
        <div className="space-y-4">
          <StatCard label="Total Income" value={r.total_income} />
          <ReportBarChart
            data={r.months.map((m) => ({ label: m.month, value: Number(m.total) }))}
          />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Month</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {r.months.map((m) => (
                <TableRow key={m.month}>
                  <TableCell>{m.month}</TableCell>
                  <TableCell className="text-right">{money(m.total)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      );
    }

    case "category-expenses": {
      const r = report as CategoryWiseExpenseReport;
      return (
        <div className="space-y-4">
          <StatCard label="Total Expenses" value={r.total_expenses} />
          <ReportBarChart
            data={r.categories.map((c) => ({ label: c.category, value: Number(c.total) }))}
          />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {r.categories.map((c) => (
                <TableRow key={c.category}>
                  <TableCell>{c.category}</TableCell>
                  <TableCell className="text-right">{money(c.total)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      );
    }

    default:
      return null;
  }
}
