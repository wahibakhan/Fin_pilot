"use client";

import { ArrowDownLeft, ArrowUpRight } from "lucide-react";

import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { DashboardSummary } from "@/lib/types";

interface RecentTransactionsProps {
  transactions: DashboardSummary["recent_transactions"];
}

export function RecentTransactions({ transactions }: RecentTransactionsProps) {
  return (
    <Card className="overflow-hidden border-border/60 py-0 shadow-sm">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/40 hover:bg-muted/40">
            <TableHead>Type</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Date</TableHead>
            <TableHead className="text-right">Amount</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                No transactions yet.
              </TableCell>
            </TableRow>
          ) : null}
          {transactions.map((t) => {
            const isIncome = t.type === "income";
            return (
              <TableRow key={`${t.type}-${t.id}`}>
                <TableCell>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
                      isIncome ? "bg-income/10 text-income" : "bg-expense/10 text-expense"
                    )}
                  >
                    {isIncome ? (
                      <ArrowUpRight className="size-3" />
                    ) : (
                      <ArrowDownLeft className="size-3" />
                    )}
                    {isIncome ? "Income" : "Expense"}
                  </span>
                </TableCell>
                <TableCell className="font-medium">{t.label}</TableCell>
                <TableCell className="text-muted-foreground">{t.category ?? "—"}</TableCell>
                <TableCell className="text-muted-foreground">{t.date}</TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums",
                    isIncome ? "text-income" : "text-expense"
                  )}
                >
                  {isIncome ? "+" : "-"}
                  {Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Card>
  );
}
