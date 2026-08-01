import { Sparkles } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { AIChatPanel } from "@/components/chat/AIChatPanel";

export default function AIAssistantPage() {
  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-6">
      <PageHeader
        icon={Sparkles}
        title="AI Assistant"
        description="Ask FinPilot to add records, generate reports, or analyze your books in plain English."
      />
      <div className="min-h-0 flex-1">
        <AIChatPanel />
      </div>
    </div>
  );
}
