import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetchMock = vi.fn();
vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>(
    "@/lib/api-client"
  );
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => apiFetchMock(...args),
  };
});

import { AIChatPanel } from "@/components/chat/AIChatPanel";
import { ApiError } from "@/lib/api-client";

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("AIChatPanel", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
  });

  it("sends a message and shows a proposed action with Confirm/Reject", async () => {
    apiFetchMock.mockResolvedValueOnce({
      interaction_id: "int-1",
      conversation_id: "conv-1",
      status: "proposed",
      message: "I'll add an expense: Office Rent — 50000 on 2026-07-01 (category: Rent). Confirm?",
      proposed_action: { action: "add_expense", title: "Office Rent", amount: 50000, date: "2026-07-01", category: "Rent" },
      data: null,
    });

    const user = userEvent.setup();
    renderWithClient(<AIChatPanel />);

    await user.type(screen.getByPlaceholderText(/ask finpilot/i), "Add office rent 50000 for July");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText(/Add expense: Office Rent/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reject/i })).toBeInTheDocument();
  });

  it("confirming a proposal calls the confirm endpoint and shows the result", async () => {
    apiFetchMock.mockResolvedValueOnce({
      interaction_id: "int-1",
      conversation_id: "conv-1",
      status: "proposed",
      message: "Confirm?",
      proposed_action: { action: "add_expense", title: "Office Rent", amount: 50000, date: "2026-07-01", category: "Rent" },
      data: null,
    });
    apiFetchMock.mockResolvedValueOnce({
      interaction_id: "int-1",
      conversation_id: "conv-1",
      status: "confirmed",
      message: "Added expense 'Office Rent' for 50000 on 2026-07-01.",
      proposed_action: null,
      data: { id: "exp-1" },
    });

    const user = userEvent.setup();
    renderWithClient(<AIChatPanel />);

    await user.type(screen.getByPlaceholderText(/ask finpilot/i), "Add office rent 50000 for July");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await screen.findByRole("button", { name: /confirm/i });

    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(await screen.findByText(/Added expense 'Office Rent'/i)).toBeInTheDocument();
    expect(apiFetchMock).toHaveBeenCalledWith(
      "/ai/interactions/int-1/confirm",
      expect.objectContaining({ method: "POST" })
    );
    // Confirm/Reject buttons are gone once resolved.
    expect(screen.queryByRole("button", { name: /^confirm$/i })).not.toBeInTheDocument();
  });

  it("shows the unavailable state and disables input on a 503", async () => {
    apiFetchMock.mockRejectedValueOnce(new ApiError(503, "AI provider unavailable"));

    const user = userEvent.setup();
    renderWithClient(<AIChatPanel />);

    await user.type(screen.getByPlaceholderText(/ask finpilot/i), "hello");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText(/ai assistant unavailable/i)).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText(/ask finpilot/i)).toBeDisabled();
  });
});
