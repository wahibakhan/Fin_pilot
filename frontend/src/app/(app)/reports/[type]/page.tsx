"use client";

import { use, useState } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Input } from "@/components/ui/input";
import { ReportView } from "@/components/tables/ReportView";
import { useReport } from "@/hooks/useReports";
import { ApiError } from "@/lib/api-client";
import { isReportType, REPORT_TYPES } from "@/lib/report-types";

function defaultRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const toIso = (d: Date) => d.toISOString().slice(0, 10);
  return { from: toIso(start), to: toIso(end) };
}

export default function ReportPage({ params }: { params: Promise<{ type: string }> }) {
  const { type } = use(params);

  if (!isReportType(type)) {
    notFound();
  }

  const meta = REPORT_TYPES.find((r) => r.type === type)!;
  const initial = defaultRange();
  const [dateFrom, setDateFrom] = useState(initial.from);
  const [dateTo, setDateTo] = useState(initial.to);

  const { data, error, isLoading } = useReport(type, dateFrom, dateTo);

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/reports"
          className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          All reports
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{meta.label}</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">{meta.description}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border/60 bg-card px-4 py-3 shadow-sm">
        <span className="text-sm font-medium text-muted-foreground">Period</span>
        <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="w-40" />
        <span className="text-muted-foreground">to</span>
        <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="w-40" />
      </div>

      {isLoading ? <p className="text-muted-foreground">Loading…</p> : null}

      {error instanceof ApiError && error.status === 403 ? (
        <p className="text-destructive">
          You don&apos;t have permission to view this report.
        </p>
      ) : null}
      {error instanceof ApiError && error.status === 400 ? (
        <p className="text-destructive">{error.message}</p>
      ) : null}
      {error instanceof ApiError && error.status !== 403 && error.status !== 400 ? (
        <p className="text-destructive">Something went wrong loading this report.</p>
      ) : null}

      {data ? <ReportView type={type} report={data} /> : null}
    </div>
  );
}
