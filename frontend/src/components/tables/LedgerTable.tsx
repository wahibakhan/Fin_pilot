"use client";

import { useState } from "react";
import { ArrowDown, ArrowDownLeft, ArrowUp, ArrowUpRight, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
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
import { useLedger, type LedgerFilters } from "@/hooks/useLedger";

const ALL_CATEGORIES = "__all__";

export function LedgerTable() {
  const [filters, setFilters] = useState<LedgerFilters>({
    page: 1,
    page_size: 50,
    sort_by: "date",
    sort_dir: "desc",
  });
  const { data: categories } = useCategories();
  const { data, isLoading } = useLedger(filters);

  function updateFilter<K extends keyof LedgerFilters>(key: K, value: LedgerFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }

  function goToPage(page: number) {
    setFilters((prev) => ({ ...prev, page }));
  }

  function toggleSort(column: "date" | "amount") {
    setFilters((prev) => ({
      ...prev,
      sort_by: column,
      sort_dir: prev.sort_by === column && prev.sort_dir === "desc" ? "asc" : "desc",
      page: 1,
    }));
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / (filters.page_size ?? 50))) : 1;
  const currentPage = filters.page ?? 1;

  function SortIcon({ column }: { column: "date" | "amount" }) {
    if (filters.sort_by !== column) return null;
    return filters.sort_dir === "asc" ? (
      <ArrowUp className="ml-1 inline size-3" />
    ) : (
      <ArrowDown className="ml-1 inline size-3" />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <div className="relative max-w-xs flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search ledger…"
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
              <TableHead>Type</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Category</TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => toggleSort("date")}
              >
                Date
                <SortIcon column="date" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none text-right"
                onClick={() => toggleSort("amount")}
              >
                Amount
                <SortIcon column="amount" />
              </TableHead>
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
                  No ledger entries found.
                </TableCell>
              </TableRow>
            ) : null}
            {data?.items.map((entry) => {
              const isIncome = entry.type === "income";
              return (
                <TableRow key={`${entry.type}-${entry.id}`}>
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
                  <TableCell className="font-medium">{entry.label}</TableCell>
                  <TableCell className="text-muted-foreground">{entry.category ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{entry.date}</TableCell>
                  <TableCell
                    className={cn(
                      "text-right tabular-nums",
                      isIncome ? "text-income" : "text-expense"
                    )}
                  >
                    {isIncome ? "+" : "-"}
                    {Number(entry.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Card>

      {data ? (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{data.total} entries total</p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => goToPage(currentPage - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => goToPage(currentPage + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
