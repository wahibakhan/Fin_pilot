"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { Expense, ExpensePage } from "@/lib/types";
import type { ExpenseFormValues } from "@/components/forms/ExpenseForm";

export interface ExpenseFilters {
  q?: string;
  category_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

function buildQuery(filters: ExpenseFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.category_id) params.set("category_id", filters.category_id);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return params.toString();
}

export function useExpenses(filters: ExpenseFilters = {}) {
  return useQuery<ExpensePage>({
    queryKey: ["expenses", filters],
    queryFn: () => apiFetch<ExpensePage>(`/expenses?${buildQuery(filters)}`),
    placeholderData: (previousData) => previousData,
  });
}

function invalidateExpenseDerivedData(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["expenses"] });
  void queryClient.invalidateQueries({ queryKey: ["ledger"] });
  void queryClient.invalidateQueries({ queryKey: ["reports"] });
}

export function useCreateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: ExpenseFormValues) =>
      apiFetch<Expense>("/expenses", {
        method: "POST",
        body: JSON.stringify(values),
      }),
    onSuccess: () => invalidateExpenseDerivedData(queryClient),
  });
}

export function useUpdateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, values }: { id: string; values: ExpenseFormValues }) =>
      apiFetch<Expense>(`/expenses/${id}`, {
        method: "PATCH",
        body: JSON.stringify(values),
      }),
    onSuccess: () => invalidateExpenseDerivedData(queryClient),
  });
}

export function useDeleteExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/expenses/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateExpenseDerivedData(queryClient),
  });
}
