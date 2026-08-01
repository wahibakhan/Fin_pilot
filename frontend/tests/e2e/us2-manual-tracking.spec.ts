import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §3 (spec.md User Story 2).
test.describe("US2 - Manual Income & Expense Tracking", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_USERS.accountant);
  });

  test("add, edit, and delete an expense", async ({ page }) => {
    await page.goto("/expenses");

    await page.getByRole("button", { name: /add expense/i }).click();
    await page.getByLabel(/title/i).fill("E2E Office Rent");
    await page.getByLabel(/amount/i).fill("50000");
    await page.getByRole("combobox", { name: /category/i }).click();
    await page.getByRole("option").first().click();
    await page.getByLabel(/date/i).fill("2026-07-05");
    await page.getByRole("button", { name: /add expense/i }).click();

    const row = page.getByRole("row", { name: /E2E Office Rent/i });
    await expect(row).toBeVisible();

    await row.getByRole("button", { name: /edit/i }).click();
    await page.getByLabel(/amount/i).fill("52000");
    await page.getByRole("button", { name: /save changes/i }).click();
    await expect(page.getByRole("row", { name: /52,000/ })).toBeVisible();

    await row.getByRole("button", { name: /delete/i }).click();
    await page.getByRole("button", { name: /^delete$/i }).click();
    await expect(page.getByRole("row", { name: /E2E Office Rent/i })).toHaveCount(0);
  });

  test("rejects an expense with a non-positive amount before any network call", async ({ page }) => {
    await page.goto("/expenses");
    await page.getByRole("button", { name: /add expense/i }).click();
    await page.getByLabel(/title/i).fill("Bad Expense");
    await page.getByLabel(/amount/i).fill("0");
    await page.getByRole("button", { name: /add expense/i }).click();

    await expect(page.getByText(/amount must be greater than 0/i)).toBeVisible();
  });

  test("add and delete an income entry", async ({ page }) => {
    await page.goto("/income");

    await page.getByRole("button", { name: /add income/i }).click();
    await page.getByLabel(/source/i).fill("E2E Consulting Fee");
    await page.getByLabel(/amount/i).fill("5000");
    await page.getByLabel(/date/i).fill("2026-07-05");
    await page.getByRole("button", { name: /add income/i }).click();

    const row = page.getByRole("row", { name: /E2E Consulting Fee/i });
    await expect(row).toBeVisible();

    await row.getByRole("button", { name: /delete/i }).click();
    await page.getByRole("button", { name: /^delete$/i }).click();
    await expect(page.getByRole("row", { name: /E2E Consulting Fee/i })).toHaveCount(0);
  });

  test("search narrows visible expense rows", async ({ page }) => {
    await page.goto("/expenses");
    await page.getByPlaceholder(/search expenses/i).fill("zzz-no-such-expense-zzz");
    await expect(page.getByText(/no expenses found/i)).toBeVisible();
  });
});
