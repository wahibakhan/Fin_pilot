"use client";

import { ArrowDownRight, ArrowUpRight, Scale } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

function money(value: string): string {
  return Number(value).toLocaleString(undefined, { minimumFractionDigits: 2 });
}

interface StatCardsProps {
  totalIncome: string;
  totalExpenses: string;
  netProfit: string;
}

export function StatCards({ totalIncome, totalExpenses, netProfit }: StatCardsProps) {
  const profitPositive = Number(netProfit) >= 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <StatCard
        label="Total Income"
        value={money(totalIncome)}
        icon={ArrowUpRight}
        tone="income"
      />
      <StatCard
        label="Total Expenses"
        value={money(totalExpenses)}
        icon={ArrowDownRight}
        tone="expense"
      />
      <StatCard
        label="Net Profit"
        value={money(netProfit)}
        icon={Scale}
        tone={profitPositive ? "income" : "expense"}
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string;
  icon: typeof ArrowUpRight;
  tone: "income" | "expense";
}) {
  return (
    <Card className="overflow-hidden border-border/60 shadow-sm">
      <CardContent className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="mt-1.5 truncate text-2xl font-semibold tabular-nums tracking-tight">
            {value}
          </p>
        </div>
        <div
          className={cn(
            "flex size-11 shrink-0 items-center justify-center rounded-xl",
            tone === "income"
              ? "bg-income/10 text-income"
              : "bg-expense/10 text-expense"
          )}
        >
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  );
}
