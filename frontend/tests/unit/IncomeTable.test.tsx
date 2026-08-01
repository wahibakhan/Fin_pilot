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

import { IncomeTable } from "@/components/tables/IncomeTable";

const incomePage = {
  items: [
    { id: "inc-1", source: "Consulting Fee", amount: "5000.00", date: "2026-07-01", description: null, created_by: "u1", created_via: "manual", created_at: "", updated_at: "" },
  ],
  total: 1,
  page: 1,
  page_size: 25,
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("IncomeTable", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
    apiFetchMock.mockResolvedValue(incomePage);
  });

  it("renders income rows", async () => {
    renderWithClient(<IncomeTable canDelete={true} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(await screen.findByText("Consulting Fee")).toBeInTheDocument();
  });

  it("hides Delete when canDelete is false", async () => {
    renderWithClient(<IncomeTable canDelete={false} onEdit={vi.fn()} onDelete={vi.fn()} />);
    await screen.findByText("Consulting Fee");
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
  });

  it("searching narrows the query sent to the API", async () => {
    const user = userEvent.setup();
    renderWithClient(<IncomeTable canDelete={true} onEdit={vi.fn()} onDelete={vi.fn()} />);
    await screen.findByText("Consulting Fee");

    await user.type(screen.getByPlaceholderText(/search income/i), "consulting");

    await waitFor(() => {
      const lastCall = apiFetchMock.mock.calls.at(-1)?.[0] as string;
      expect(lastCall).toContain("q=consulting");
    });
  });

  it("calls onDelete with the clicked income entry", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    renderWithClient(<IncomeTable canDelete={true} onEdit={vi.fn()} onDelete={onDelete} />);
    await screen.findByText("Consulting Fee");

    await user.click(screen.getByRole("button", { name: /delete/i }));
    expect(onDelete).toHaveBeenCalledWith(expect.objectContaining({ id: "inc-1" }));
  });
});
