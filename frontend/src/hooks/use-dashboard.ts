"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { DashboardSummary } from "@/lib/types";

export function useDashboard(period?: string) {
  return useQuery<DashboardSummary>({
    queryKey: ["reports", "dashboard-summary", period],
    queryFn: () =>
      apiFetch<DashboardSummary>(
        `/dashboard/summary${period ? `?period=${period}` : ""}`
      ),
  });
}
