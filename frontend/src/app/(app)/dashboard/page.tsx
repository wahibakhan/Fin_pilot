"use client";

import { useState } from "react";
import { LayoutDashboard } from "lucide-react";

import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/layout/page-header";
import { DashboardCharts } from "@/components/charts/DashboardCharts";
import { MonthlySummary } from "@/components/charts/MonthlySummary";
import { StatCards } from "@/components/charts/StatCards";
import { RecentTransactions } from "@/components/tables/RecentTransactions";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useDashboard } from "@/hooks/use-dashboard";

function currentPeriod(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export default function DashboardPage() {
  const [period, setPeriod] = useState(currentPeriod());
  const { data: user } = useCurrentUser();
  const { data, isLoading } = useDashboard(period);

  return (
    <div className="space-y-6">
      <PageHeader
        icon={LayoutDashboard}
        title={user ? `Welcome back, ${user.full_name.split(" ")[0]}` : "Dashboard"}
        description="Your business's financial snapshot at a glance."
        actions={
          <Input
            type="month"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="w-40"
          />
        }
      />

      {isLoading || !data ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : (
        <>
          <StatCards
            totalIncome={data.total_income}
            totalExpenses={data.total_expenses}
            netProfit={data.net_profit}
          />

          <DashboardCharts
            monthlySummary={data.monthly_summary}
            expenseCategories={data.expense_categories}
          />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <h2 className="mb-2 text-sm font-semibold text-foreground">Monthly Summary</h2>
              <MonthlySummary months={data.monthly_summary} />
            </div>
            <div>
              <h2 className="mb-2 text-sm font-semibold text-foreground">
                Recent Transactions
              </h2>
              <RecentTransactions transactions={data.recent_transactions} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
