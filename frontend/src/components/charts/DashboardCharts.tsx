"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/card";
import { ReportBarChart } from "@/components/charts/ReportCharts";
import type { DashboardSummary } from "@/lib/types";

function formatMoney(value: number): string {
  return value.toLocaleString(undefined, { minimumFractionDigits: 2 });
}

interface DashboardChartsProps {
  monthlySummary: DashboardSummary["monthly_summary"];
  expenseCategories: DashboardSummary["expense_categories"];
}

export function DashboardCharts({ monthlySummary, expenseCategories }: DashboardChartsProps) {
  const trendData = monthlySummary.map((m) => ({
    month: m.month,
    Income: Number(m.income),
    Expenses: Number(m.expenses),
  }));
  const categoryData = expenseCategories.map((c) => ({
    label: c.category,
    value: Number(c.total),
  }));

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card className="border-border/60 shadow-sm">
        <div className="px-1">
          <h2 className="mb-2 px-3 pt-1 text-sm font-semibold">Income vs Expenses</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                <XAxis dataKey="month" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip formatter={(value) => formatMoney(Number(value))} cursor={{ fill: "var(--muted)" }} />
                <Legend />
                <Bar dataKey="Income" fill="var(--income)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Expenses" fill="var(--expense)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </Card>

      <Card className="border-border/60 shadow-sm">
        <div className="px-1">
          <h2 className="mb-2 px-3 pt-1 text-sm font-semibold">Expenses by Category</h2>
          <ReportBarChart data={categoryData} />
        </div>
      </Card>
    </div>
  );
}
