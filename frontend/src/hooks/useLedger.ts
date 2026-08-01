"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { LedgerPage } from "@/lib/types";

export interface LedgerFilters {
  q?: string;
  category_id?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: "date" | "amount";
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

function buildQuery(filters: LedgerFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.category_id) params.set("category_id", filters.category_id);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  params.set("sort_by", filters.sort_by ?? "date");
  params.set("sort_dir", filters.sort_dir ?? "desc");
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 50));
  return params.toString();
}

export function useLedger(filters: LedgerFilters = {}) {
  return useQuery<LedgerPage>({
    queryKey: ["ledger", filters],
    queryFn: () => apiFetch<LedgerPage>(`/ledger?${buildQuery(filters)}`),
    placeholderData: (previousData) => previousData,
  });
}
