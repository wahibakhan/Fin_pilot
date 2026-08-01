"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
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
import { useAuditLogs, type AuditLogFilters } from "@/hooks/use-audit-logs";
import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { AuditEntityType } from "@/lib/types";

const ALL_ENTITY_TYPES = "__all__";
const ENTITY_TYPES: AuditEntityType[] = ["expense", "income", "category", "user"];

const ACTION_STYLES: Record<string, string> = {
  create: "bg-income/10 text-income",
  update: "bg-chart-4/15 text-amber-600 dark:text-chart-4",
  delete: "bg-expense/10 text-expense",
};

export default function AuditLogPage() {
  const [filters, setFilters] = useState<AuditLogFilters>({ page: 1, page_size: 25 });
  const { data, error, isLoading } = useAuditLogs(filters);

  if (error instanceof ApiError && error.status === 403) {
    return (
      <div className="space-y-6">
        <PageHeader icon={ShieldCheck} title="Audit Log" />
        <p className="text-destructive">You don&apos;t have permission to view the audit log.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        icon={ShieldCheck}
        title="Audit Log"
        description="Every create, update, and delete — by a user or the AI assistant."
      />

      <Select
        value={filters.entity_type ?? ALL_ENTITY_TYPES}
        onValueChange={(value) =>
          setFilters((prev) => ({
            ...prev,
            entity_type: !value || value === ALL_ENTITY_TYPES ? undefined : (value as AuditEntityType),
            page: 1,
          }))
        }
      >
        <SelectTrigger className="w-48">
          <SelectValue placeholder="All entity types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_ENTITY_TYPES}>All entity types</SelectItem>
          {ENTITY_TYPES.map((type) => (
            <SelectItem key={type} value={type} className="capitalize">
              {type}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Card className="overflow-hidden border-border/60 py-0 shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead>Actor</TableHead>
              <TableHead>Entity</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>When</TableHead>
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
                  No audit entries found.
                </TableCell>
              </TableRow>
            ) : null}
            {data?.items.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>
                  <Badge variant={entry.actor_type === "ai" ? "default" : "secondary"}>
                    {entry.actor_type === "ai" ? "AI" : "User"}
                  </Badge>
                </TableCell>
                <TableCell className="capitalize text-muted-foreground">
                  {entry.entity_type} <span className="text-xs">({entry.entity_id.slice(0, 8)}…)</span>
                </TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize",
                      ACTION_STYLES[entry.action] ?? "bg-muted text-muted-foreground"
                    )}
                  >
                    {entry.action}
                  </span>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(entry.created_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {data ? (
        <p className="text-sm text-muted-foreground">{data.total} entries total</p>
      ) : null}
    </div>
  );
}
