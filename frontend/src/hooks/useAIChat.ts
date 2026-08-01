"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch, ApiError } from "@/lib/api-client";
import type { AIChatResponse } from "@/lib/types";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  proposedAction?: {
    interactionId: string;
    action: Record<string, unknown>;
    resolved: boolean;
  };
}

function randomId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);
}

export function useAIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [unavailable, setUnavailable] = useState(false);
  const queryClient = useQueryClient();

  function invalidateFinancialData() {
    void queryClient.invalidateQueries({ queryKey: ["expenses"] });
    void queryClient.invalidateQueries({ queryKey: ["income"] });
    void queryClient.invalidateQueries({ queryKey: ["ledger"] });
    void queryClient.invalidateQueries({ queryKey: ["reports"] });
    void queryClient.invalidateQueries({ queryKey: ["categories"] });
  }

  function appendAssistantMessage(data: AIChatResponse) {
    setConversationId(data.conversation_id);
    setMessages((prev) => [
      ...prev,
      {
        id: randomId(),
        role: "assistant",
        content: data.message,
        proposedAction:
          data.status === "proposed" && data.proposed_action
            ? { interactionId: data.interaction_id, action: data.proposed_action, resolved: false }
            : undefined,
      },
    ]);
  }

  const sendMessage = useMutation({
    mutationFn: (message: string) =>
      apiFetch<AIChatResponse>("/ai/chat", {
        method: "POST",
        body: JSON.stringify({ message, conversation_id: conversationId }),
      }),
    onSuccess: (data) => {
      setUnavailable(false);
      appendAssistantMessage(data);
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 503) {
        setUnavailable(true);
      } else {
        setMessages((prev) => [
          ...prev,
          { id: randomId(), role: "assistant", content: "Sorry, something went wrong." },
        ]);
      }
    },
  });

  function resolveProposal(interactionId: string, data: AIChatResponse) {
    setMessages((prev) =>
      prev.map((m) =>
        m.proposedAction?.interactionId === interactionId
          ? { ...m, proposedAction: { ...m.proposedAction, resolved: true } }
          : m
      )
    );
    appendAssistantMessage(data);
    invalidateFinancialData();
  }

  const confirmMutation = useMutation({
    mutationFn: (interactionId: string) =>
      apiFetch<AIChatResponse>(`/ai/interactions/${interactionId}/confirm`, { method: "POST" }),
    onSuccess: (data, interactionId) => resolveProposal(interactionId, data),
  });

  const rejectMutation = useMutation({
    mutationFn: (interactionId: string) =>
      apiFetch<AIChatResponse>(`/ai/interactions/${interactionId}/reject`, { method: "POST" }),
    onSuccess: (data, interactionId) => resolveProposal(interactionId, data),
  });

  function send(text: string) {
    setMessages((prev) => [...prev, { id: randomId(), role: "user", content: text }]);
    sendMessage.mutate(text);
  }

  return {
    messages,
    send,
    isSending: sendMessage.isPending,
    confirm: (interactionId: string) => confirmMutation.mutate(interactionId),
    reject: (interactionId: string) => rejectMutation.mutate(interactionId),
    isResolving: confirmMutation.isPending || rejectMutation.isPending,
    unavailable,
  };
}
