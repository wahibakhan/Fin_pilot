"use client";

import Link from "next/link";
import {
  ArrowRight,
  FileBarChart2,
  FileText,
  Landmark,
  PieChart,
  Scale,
  TrendingUp,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { useCurrentUser } from "@/hooks/use-current-user";
import { can } from "@/lib/rbac";
import { REPORT_TYPES } from "@/lib/report-types";
import type { ReportType } from "@/lib/types";

const REPORT_ICONS: Record<ReportType, LucideIcon> = {
  "profit-and-loss": TrendingUp,
  "balance-sheet": Scale,
  "trial-balance": Landmark,
  "cash-flow": Wallet,
  "monthly-expenses": FileBarChart2,
  income: FileText,
  "category-expenses": PieChart,
};

export default function ReportsIndexPage() {
  const { data: user } = useCurrentUser();
  const visible = REPORT_TYPES.filter(
    (r) => !r.requires || (user && can(user.role, r.requires))
  );

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FileBarChart2}
        title="Reports"
        description="Financial statements generated live from your ledger."
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((r) => {
          const Icon = REPORT_ICONS[r.type];
          return (
            <Link key={r.type} href={`/reports/${r.type}`}>
              <Card className="group h-full border-border/60 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
                <CardContent className="flex items-start gap-3.5">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Icon className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <h2 className="text-sm font-semibold">{r.label}</h2>
                      <ArrowRight className="size-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{r.description}</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
