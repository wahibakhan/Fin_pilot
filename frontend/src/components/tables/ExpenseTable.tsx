"use client";

import { useState } from "react";
import { Pencil, Search, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useCategories } from "@/hooks/use-categories";
import { useExpenses, type ExpenseFilters } from "@/hooks/useExpenses";
import type { Expense } from "@/lib/types";

interface ExpenseTableProps {
  canDelete: boolean;
  onEdit: (expense: Expense) => void;
  onDelete: (expense: Expense) => void;
}

const ALL_CATEGORIES = "__all__";

export function ExpenseTable({ canDelete, onEdit, onDelete }: ExpenseTableProps) {
  const [filters, setFilters] = useState<ExpenseFilters>({ page: 1, page_size: 25 });
  const { data: categories } = useCategories();
  const { data, isLoading } = useExpenses(filters);

  function updateFilter<K extends keyof ExpenseFilters>(key: K, value: ExpenseFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <div className="relative max-w-xs flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search expenses…"
            className="pl-8"
            value={filters.q ?? ""}
            onChange={(e) => updateFilter("q", e.target.value || undefined)}
          />
        </div>
        <Select
          value={filters.category_id ?? ALL_CATEGORIES}
          onValueChange={(value) =>
            updateFilter("category_id", !value || value === ALL_CATEGORIES ? undefined : value)
          }
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_CATEGORIES}>All categories</SelectItem>
            {categories?.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
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
              <TableHead>Title</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="w-1" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : null}
            {!isLoading && data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No expenses found.
                </TableCell>
              </TableRow>
            ) : null}
            {data?.items.map((expense) => {
              const category = categories?.find((c) => c.id === expense.category_id);
              return (
                <TableRow key={expense.id}>
                  <TableCell className="font-medium">{expense.title}</TableCell>
                  <TableCell className="text-muted-foreground">{category?.name ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{expense.date}</TableCell>
                  <TableCell className="text-right text-expense tabular-nums">
                    {Number(expense.amount).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon-sm" onClick={() => onEdit(expense)}>
                      <Pencil className="size-3.5" />
                      <span className="sr-only">Edit</span>
                    </Button>
                    {canDelete ? (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => onDelete(expense)}
                      >
                        <Trash2 className="size-3.5" />
                        <span className="sr-only">Delete</span>
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Card>

      {data ? (
        <p className="text-sm text-muted-foreground">
          {data.total} expense{data.total === 1 ? "" : "s"} total
        </p>
      ) : null}
    </div>
  );
}
