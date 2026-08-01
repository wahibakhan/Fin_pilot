import { BookOpenText } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { LedgerTable } from "@/components/tables/LedgerTable";

export default function LedgerPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        icon={BookOpenText}
        title="Ledger"
        description="Every income and expense entry in one searchable history."
      />
      <LedgerTable />
    </div>
  );
}
