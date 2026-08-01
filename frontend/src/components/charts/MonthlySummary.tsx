"use client";

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

function money(value: string): string {
  return Number(value).toLocaleString(undefined, { minimumFractionDigits: 2 });
}

interface MonthlySummaryProps {
  months: DashboardSummary["monthly_summary"];
}

export function MonthlySummary({ months }: MonthlySummaryProps) {
  return (
    <Card className="overflow-hidden border-border/60 py-0 shadow-sm">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/40 hover:bg-muted/40">
            <TableHead>Month</TableHead>
            <TableHead className="text-right">Income</TableHead>
            <TableHead className="text-right">Expenses</TableHead>
            <TableHead className="text-right">Net</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {months.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No data for this period.
              </TableCell>
            </TableRow>
          ) : null}
          {months.map((m) => {
            const net = Number(m.income) - Number(m.expenses);
            return (
              <TableRow key={m.month}>
                <TableCell className="font-medium">{m.month}</TableCell>
                <TableCell className="text-right text-income tabular-nums">
                  {money(m.income)}
                </TableCell>
                <TableCell className="text-right text-expense tabular-nums">
                  {money(m.expenses)}
                </TableCell>
                <TableCell
                  className={cn(
                    "text-right font-medium tabular-nums",
                    net >= 0 ? "text-income" : "text-expense"
                  )}
                >
                  {money(String(net))}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Card>
  );
}
