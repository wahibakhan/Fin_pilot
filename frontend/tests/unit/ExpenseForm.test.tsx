import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCategoriesMock = vi.fn();
vi.mock("@/hooks/use-categories", () => ({
  useCategories: () => useCategoriesMock(),
}));

import { ExpenseForm } from "@/components/forms/ExpenseForm";
import type { Expense } from "@/lib/types";

const categories = [
  { id: "cat-1", name: "Rent", type: "expense" as const, is_archived: false },
  { id: "cat-2", name: "Utilities", type: "expense" as const, is_archived: false },
];

describe("ExpenseForm", () => {
  beforeEach(() => {
    useCategoriesMock.mockReturnValue({ data: categories, isLoading: false });
  });

  it("blocks submit and shows field errors for missing title and zero amount, without calling onSubmit", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ExpenseForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/amount/i), "0");
    await user.click(screen.getByRole("button", { name: /add expense/i }));

    expect(await screen.findByText(/title is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/amount must be greater than 0/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits valid values, including the amount as a string", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ExpenseForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/title/i), "Office Rent");
    await user.clear(screen.getByLabelText(/amount/i));
    await user.type(screen.getByLabelText(/amount/i), "50000");
    await user.type(screen.getByLabelText(/date/i), "2026-07-01");

    // shadcn/base-ui Select isn't a native <select>; open it and pick an option.
    await user.click(screen.getByRole("combobox", { name: /category/i }));
    await user.click(await screen.findByRole("option", { name: "Rent" }));

    await user.click(screen.getByRole("button", { name: /add expense/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Office Rent",
        amount: "50000",
        category_id: "cat-1",
        date: "2026-07-01",
      })
    );
  });

  it("pre-fills fields from an existing expense in edit mode", () => {
    const expense: Expense = {
      id: "exp-1",
      title: "Office Rent",
      amount: "50000.00",
      category_id: "cat-1",
      date: "2026-07-01",
      description: "July rent",
      created_by: "user-1",
      created_via: "manual",
      created_at: "2026-07-01T00:00:00Z",
      updated_at: "2026-07-01T00:00:00Z",
    };

    render(<ExpenseForm expense={expense} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText(/title/i)).toHaveValue("Office Rent");
    expect(screen.getByLabelText(/amount/i)).toHaveValue(50000);
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
  });
});
