"use client";

import { useState } from "react";
import { AlertTriangle, Send, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProposedActionCard } from "@/components/chat/ProposedActionCard";
import { useAIChat } from "@/hooks/useAIChat";
import { cn } from "@/lib/utils";

export function AIChatPanel() {
  const { messages, send, isSending, confirm, reject, isResolving, unavailable } = useAIChat();
  const [draft, setDraft] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || unavailable) return;
    send(text);
    setDraft("");
  }

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-border/60 bg-card shadow-sm">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 py-10 text-center">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Sparkles className="size-6" />
            </div>
            <p className="max-w-xs text-sm text-muted-foreground">
              Try &ldquo;Add office rent 50000 for July&rdquo; or &ldquo;Show top five
              expenses&rdquo;.
            </p>
          </div>
        ) : null}
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}
          >
            {message.proposedAction ? (
              <ProposedActionCard
                interactionId={message.proposedAction.interactionId}
                action={message.proposedAction.action}
                resolved={message.proposedAction.resolved}
                isResolving={isResolving}
                onConfirm={confirm}
                onReject={reject}
              />
            ) : (
              <div className={cn("flex max-w-md items-end gap-2", message.role === "user" && "flex-row-reverse")}>
                {message.role === "assistant" ? (
                  <div className="mb-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Sparkles className="size-3.5" />
                  </div>
                ) : null}
                <div
                  className={cn(
                    "rounded-2xl px-3.5 py-2 text-sm shadow-sm",
                    message.role === "user"
                      ? "rounded-br-sm bg-primary text-primary-foreground"
                      : "rounded-bl-sm bg-muted text-foreground"
                  )}
                >
                  {message.content}
                </div>
              </div>
            )}
          </div>
        ))}
        {isSending ? (
          <div className="flex items-center gap-2">
            <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Sparkles className="size-3.5" />
            </div>
            <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-muted px-3.5 py-2.5">
              <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
              <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
              <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60" />
            </div>
          </div>
        ) : null}
      </div>

      {unavailable ? (
        <p className="flex items-center gap-2 border-t bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="size-4 shrink-0" />
          AI assistant unavailable — please use manual entry for now.
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t p-3">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask FinPilot AI…"
          disabled={unavailable || isSending}
        />
        <Button
          type="submit"
          size="icon"
          aria-label="Send"
          disabled={unavailable || isSending || !draft.trim()}
        >
          <Send className="size-4" />
        </Button>
      </form>
    </div>
  );
}
