"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";

function describeAction(action: Record<string, unknown>): string {
  switch (action.action) {
    case "add_expense":
      return `Add expense: ${action.title} — ${action.amount} on ${action.date} (${action.category})`;
    case "add_income":
      return `Add income: ${action.source} — ${action.amount} on ${action.date}`;
    case "delete_expense":
      return `Delete expense: ${action.title} — ${action.amount} on ${action.date}`;
    default:
      return "Proposed action";
  }
}

interface ProposedActionCardProps {
  interactionId: string;
  action: Record<string, unknown>;
  resolved: boolean;
  isResolving: boolean;
  onConfirm: (interactionId: string) => void;
  onReject: (interactionId: string) => void;
}

export function ProposedActionCard({
  interactionId,
  action,
  resolved,
  isResolving,
  onConfirm,
  onReject,
}: ProposedActionCardProps) {
  return (
    <Card className="max-w-md">
      <CardContent className="text-sm">{describeAction(action)}</CardContent>
      {!resolved ? (
        <CardFooter className="flex justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={isResolving}
            onClick={() => onReject(interactionId)}
          >
            Reject
          </Button>
          <Button size="sm" disabled={isResolving} onClick={() => onConfirm(interactionId)}>
            Confirm
          </Button>
        </CardFooter>
      ) : null}
    </Card>
  );
}
