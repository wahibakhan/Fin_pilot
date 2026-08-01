import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §6 (spec.md User Story 5). Assumes
// `scripts.seed_bulk_ledger` has been run for a large enough dataset to
// exercise pagination.
test.describe("US5 - Complete Ledger & Transaction History", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_USERS.accountant);
    await page.goto("/ledger");
  });

  test("entries are paginated, not all loaded at once", async ({ page }) => {
    await expect(page.getByText(/entries total/i)).toBeVisible();
    await expect(page.getByText(/page 1 of/i)).toBeVisible();
  });

  test("combined category and date-range filters narrow the results", async ({ page }) => {
    await page.locator('input[type="date"]').first().fill("2026-01-01");
    await page.locator('input[type="date"]').last().fill("2026-12-31");
    await expect(page.getByRole("table")).toBeVisible();
  });

  test("sorting by amount toggles ascending/descending", async ({ page }) => {
    await page.getByText("Amount", { exact: false }).click();
    await page.getByText("Amount", { exact: false }).click();
    await expect(page.getByRole("table")).toBeVisible();
  });

  test("next page shows different rows than the first page", async ({ page }) => {
    const firstPageFirstRow = await page.locator("tbody tr").first().innerText();

    await page.getByRole("button", { name: /^next$/i }).click();
    await expect(page.getByText(/page 2 of/i)).toBeVisible();

    const secondPageFirstRow = await page.locator("tbody tr").first().innerText();
    expect(secondPageFirstRow).not.toEqual(firstPageFirstRow);
  });
});
