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

import { ExpenseTable } from "@/components/tables/ExpenseTable";

const expensePage = {
  items: [
    { id: "exp-1", title: "Office Rent", amount: "50000.00", category_id: "cat-1", date: "2026-07-01", description: null, created_by: "u1", created_via: "manual", created_at: "", updated_at: "" },
  ],
  total: 1,
  page: 1,
  page_size: 25,
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ExpenseTable", () => {
  beforeEach(() => {
    useCategoriesMock.mockReturnValue({ data: [{ id: "cat-1", name: "Rent" }] });
    apiFetchMock.mockReset();
    apiFetchMock.mockResolvedValue(expensePage);
  });

  it("renders expense rows with resolved category name", async () => {
    renderWithClient(<ExpenseTable canDelete={true} onEdit={vi.fn()} onDelete={vi.fn()} />);

    expect(await screen.findByText("Office Rent")).toBeInTheDocument();
    expect(screen.getByText("Rent")).toBeInTheDocument();
  });

  it("shows the Delete action when canDelete is true, hides it otherwise", async () => {
    const { rerender } = renderWithClient(
      <ExpenseTable canDelete={true} onEdit={vi.fn()} onDelete={vi.fn()} />
    );
    await screen.findByText("Office Rent");
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    rerender(
      <QueryClientProvider client={client}>
        <ExpenseTable canDelete={false} onEdit={vi.fn()} onDelete={vi.fn()} />
      </QueryClientProvider>
    );
    await screen.findByText("Office Rent");
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
  });

  it("searching narrows the query sent to the API", async () => {
    const user = userEvent.setup();
    renderWithClient(<ExpenseTable canDelete={true} onEdit={vi.fn()} onDelete={vi.fn()} />);
    await screen.findByText("Office Rent");

    await user.type(screen.getByPlaceholderText(/search expenses/i), "rent");

    await waitFor(() => {
      const lastCall = apiFetchMock.mock.calls.at(-1)?.[0] as string;
      expect(lastCall).toContain("q=rent");
    });
  });

  it("calls onEdit with the clicked expense", async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    renderWithClient(<ExpenseTable canDelete={true} onEdit={onEdit} onDelete={vi.fn()} />);
    await screen.findByText("Office Rent");

    await user.click(screen.getByRole("button", { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ id: "exp-1", title: "Office Rent" }));
  });
});
