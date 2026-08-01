"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { Income, IncomePage } from "@/lib/types";
import type { IncomeFormValues } from "@/components/forms/IncomeForm";

export interface IncomeFilters {
  q?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

function buildQuery(filters: IncomeFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return params.toString();
}

export function useIncome(filters: IncomeFilters = {}) {
  return useQuery<IncomePage>({
    queryKey: ["income", filters],
    queryFn: () => apiFetch<IncomePage>(`/income?${buildQuery(filters)}`),
    placeholderData: (previousData) => previousData,
  });
}

function invalidateIncomeDerivedData(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["income"] });
  void queryClient.invalidateQueries({ queryKey: ["ledger"] });
  void queryClient.invalidateQueries({ queryKey: ["reports"] });
}

export function useCreateIncome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: IncomeFormValues) =>
      apiFetch<Income>("/income", {
        method: "POST",
        body: JSON.stringify(values),
      }),
    onSuccess: () => invalidateIncomeDerivedData(queryClient),
  });
}

export function useUpdateIncome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, values }: { id: string; values: IncomeFormValues }) =>
      apiFetch<Income>(`/income/${id}`, {
        method: "PATCH",
        body: JSON.stringify(values),
      }),
    onSuccess: () => invalidateIncomeDerivedData(queryClient),
  });
}

export function useDeleteIncome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/income/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateIncomeDerivedData(queryClient),
  });
}
