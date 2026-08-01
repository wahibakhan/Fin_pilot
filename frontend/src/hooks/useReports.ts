"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AnyReport, ReportType } from "@/lib/types";

const REPORT_PATHS: Record<ReportType, string> = {
  "profit-and-loss": "/reports/profit-and-loss",
  "balance-sheet": "/reports/balance-sheet",
  "trial-balance": "/reports/trial-balance",
  "cash-flow": "/reports/cash-flow",
  "monthly-expenses": "/reports/monthly-expenses",
  income: "/reports/income",
  "category-expenses": "/reports/category-expenses",
};

export function useReport<T extends AnyReport = AnyReport>(
  type: ReportType,
  dateFrom: string,
  dateTo: string
) {
  return useQuery<T>({
    queryKey: ["reports", type, dateFrom, dateTo],
    queryFn: () =>
      apiFetch<T>(`${REPORT_PATHS[type]}?date_from=${dateFrom}&date_to=${dateTo}`),
    enabled: Boolean(dateFrom && dateTo),
    retry: false,
  });
}
