import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { IncomeForm } from "@/components/forms/IncomeForm";
import type { Income } from "@/lib/types";

describe("IncomeForm", () => {
  it("blocks submit and shows field errors for missing source and zero amount, without calling onSubmit", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<IncomeForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/amount/i), "0");
    await user.click(screen.getByRole("button", { name: /add income/i }));

    expect(await screen.findByText(/source is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/amount must be greater than 0/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits valid values, including the amount as a string", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<IncomeForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/source/i), "Consulting Fee");
    await user.clear(screen.getByLabelText(/amount/i));
    await user.type(screen.getByLabelText(/amount/i), "5000");
    await user.type(screen.getByLabelText(/date/i), "2026-07-01");
    await user.click(screen.getByRole("button", { name: /add income/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        source: "Consulting Fee",
        amount: "5000",
        date: "2026-07-01",
      })
    );
  });

  it("pre-fills fields from an existing income entry in edit mode", () => {
    const income: Income = {
      id: "inc-1",
      source: "Consulting Fee",
      amount: "5000.00",
      date: "2026-07-01",
      description: "July retainer",
      created_by: "user-1",
      created_via: "manual",
      created_at: "2026-07-01T00:00:00Z",
      updated_at: "2026-07-01T00:00:00Z",
    };

    render(<IncomeForm income={income} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText(/source/i)).toHaveValue("Consulting Fee");
    expect(screen.getByLabelText(/amount/i)).toHaveValue(5000);
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
  });
});
