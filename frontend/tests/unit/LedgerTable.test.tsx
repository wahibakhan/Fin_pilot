import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCategoriesMock = vi.fn();
vi.mock("@/hooks/use-categories", () => ({
  useCategories: () => useCategoriesMock(),
}));

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

import { LedgerTable } from "@/components/tables/LedgerTable";

const ledgerPage = {
  items: [
    {
      id: "exp-1",
      type: "expense",
      label: "Office Rent",
      amount: "50000.00",
      category: "Rent",
      date: "2026-07-01",
      description: null,
      created_via: "manual",
    },
    {
      id: "inc-1",
      type: "income",
      label: "Consulting Fee",
      amount: "5000.00",
      category: null,
      date: "2026-07-03",
      description: null,
      created_via: "manual",
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("LedgerTable", () => {
  beforeEach(() => {
    useCategoriesMock.mockReturnValue({ data: [{ id: "cat-1", name: "Rent" }] });
    apiFetchMock.mockReset();
    apiFetchMock.mockResolvedValue(ledgerPage);
  });

  it("renders both expense and income rows from a single combined fetch", async () => {
    renderWithClient(<LedgerTable />);

    expect(await screen.findByText("Office Rent")).toBeInTheDocument();
    expect(screen.getByText("Consulting Fee")).toBeInTheDocument();
    expect(screen.getByText("Income")).toBeInTheDocument();
    expect(screen.getByText("Expense")).toBeInTheDocument();
  });

  it("requests date-descending sort by default, then flips to ascending on header click", async () => {
    const user = userEvent.setup();
    renderWithClient(<LedgerTable />);
    await screen.findByText("Office Rent");

    const firstCall = apiFetchMock.mock.calls[0][0] as string;
    expect(firstCall).toContain("sort_by=date");
    expect(firstCall).toContain("sort_dir=desc");

    await user.click(screen.getByText("Date"));

    await waitFor(() => {
      const lastCall = apiFetchMock.mock.calls.at(-1)?.[0] as string;
      expect(lastCall).toContain("sort_dir=asc");
    });
  });

  it("resets to page 1 when a filter changes", async () => {
    const user = userEvent.setup();
    renderWithClient(<LedgerTable />);
    await screen.findByText("Office Rent");

    await user.type(screen.getByPlaceholderText(/search ledger/i), "rent");

    await waitFor(() => {
      const lastCall = apiFetchMock.mock.calls.at(-1)?.[0] as string;
      expect(lastCall).toContain("q=rent");
      expect(lastCall).toContain("page=1");
    });
  });
});
