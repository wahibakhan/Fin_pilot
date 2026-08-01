"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AuditEntityType, AuditLogPage } from "@/lib/types";

export interface AuditLogFilters {
  entity_type?: AuditEntityType;
  page?: number;
  page_size?: number;
}

function buildQuery(filters: AuditLogFilters): string {
  const params = new URLSearchParams();
  if (filters.entity_type) params.set("entity_type", filters.entity_type);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return params.toString();
}

export function useAuditLogs(filters: AuditLogFilters = {}) {
  return useQuery<AuditLogPage>({
    queryKey: ["audit-logs", filters],
    queryFn: () => apiFetch<AuditLogPage>(`/audit-logs?${buildQuery(filters)}`),
    placeholderData: (previousData) => previousData,
  });
}
