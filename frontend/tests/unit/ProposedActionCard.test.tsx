import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProposedActionCard } from "@/components/chat/ProposedActionCard";

describe("ProposedActionCard", () => {
  it("describes an add_expense proposal and calls onConfirm", async () => {
    const onConfirm = vi.fn();
    const onReject = vi.fn();
    const user = userEvent.setup();

    render(
      <ProposedActionCard
        interactionId="int-1"
        action={{ action: "add_expense", title: "Office Rent", amount: 50000, date: "2026-07-01", category: "Rent" }}
        resolved={false}
        isResolving={false}
        onConfirm={onConfirm}
        onReject={onReject}
      />
    );

    expect(screen.getByText(/Add expense: Office Rent/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /confirm/i }));
    expect(onConfirm).toHaveBeenCalledWith("int-1");
    expect(onReject).not.toHaveBeenCalled();
  });

  it("describes a delete_expense proposal and calls onReject", async () => {
    const onConfirm = vi.fn();
    const onReject = vi.fn();
    const user = userEvent.setup();

    render(
      <ProposedActionCard
        interactionId="int-2"
        action={{ action: "delete_expense", title: "Old Rent", amount: 1000, date: "2026-06-01" }}
        resolved={false}
        isResolving={false}
        onConfirm={onConfirm}
        onReject={onReject}
      />
    );

    expect(screen.getByText(/Delete expense: Old Rent/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /reject/i }));
    expect(onReject).toHaveBeenCalledWith("int-2");
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("hides Confirm/Reject once resolved", () => {
    render(
      <ProposedActionCard
        interactionId="int-3"
        action={{ action: "add_income", source: "Consulting", amount: 5000, date: "2026-07-01" }}
        resolved={true}
        isResolving={false}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reject/i })).not.toBeInTheDocument();
  });

  it("disables both buttons while resolving", () => {
    render(
      <ProposedActionCard
        interactionId="int-4"
        action={{ action: "add_expense", title: "Rent", amount: 100, date: "2026-07-01", category: "Rent" }}
        resolved={false}
        isResolving={true}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.getByRole("button", { name: /confirm/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /reject/i })).toBeDisabled();
  });
});
