"use client";

import { useState } from "react";
import { Pencil, Search, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useIncome, type IncomeFilters } from "@/hooks/useIncome";
import type { Income } from "@/lib/types";

interface IncomeTableProps {
  canDelete: boolean;
  onEdit: (income: Income) => void;
  onDelete: (income: Income) => void;
}

export function IncomeTable({ canDelete, onEdit, onDelete }: IncomeTableProps) {
  const [filters, setFilters] = useState<IncomeFilters>({ page: 1, page_size: 25 });
  const { data, isLoading } = useIncome(filters);

  function updateFilter<K extends keyof IncomeFilters>(key: K, value: IncomeFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <div className="relative max-w-xs flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search income…"
            className="pl-8"
            value={filters.q ?? ""}
            onChange={(e) => updateFilter("q", e.target.value || undefined)}
          />
        </div>
        <Input
          type="date"
          className="w-40"
          value={filters.date_from ?? ""}
          onChange={(e) => updateFilter("date_from", e.target.value || undefined)}
        />
        <Input
          type="date"
          className="w-40"
          value={filters.date_to ?? ""}
          onChange={(e) => updateFilter("date_to", e.target.value || undefined)}
        />
      </div>

      <Card className="overflow-hidden border-border/60 py-0 shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead>Source</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="w-1" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : null}
            {!isLoading && data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No income entries found.
                </TableCell>
              </TableRow>
            ) : null}
            {data?.items.map((income) => (
              <TableRow key={income.id}>
                <TableCell className="font-medium">{income.source}</TableCell>
                <TableCell className="text-muted-foreground">{income.date}</TableCell>
                <TableCell className="text-right text-income tabular-nums">
                  {Number(income.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </TableCell>
                <TableCell className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon-sm" onClick={() => onEdit(income)}>
                    <Pencil className="size-3.5" />
                    <span className="sr-only">Edit</span>
                  </Button>
                  {canDelete ? (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      onClick={() => onDelete(income)}
                    >
                      <Trash2 className="size-3.5" />
                      <span className="sr-only">Delete</span>
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {data ? (
        <p className="text-sm text-muted-foreground">
          {data.total} income entr{data.total === 1 ? "y" : "ies"} total
        </p>
      ) : null}
    </div>
  );
}
