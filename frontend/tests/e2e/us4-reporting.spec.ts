import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §5 (spec.md User Story 4).
test.describe("US4 - Financial Reporting", () => {
  test("accountant can generate a Profit & Loss statement reflecting seeded data", async ({ page }) => {
    await loginAs(page, DEMO_USERS.accountant);
    await page.goto("/reports/profit-and-loss");

    await expect(page.getByText("Total Income")).toBeVisible();
    await expect(page.getByText("Total Expenses")).toBeVisible();
    await expect(page.getByText("Net Profit")).toBeVisible();
  });

  test("a report for a period with no data returns a clean zero report", async ({ page }) => {
    await loginAs(page, DEMO_USERS.accountant);
    await page.goto("/reports/profit-and-loss");

    await page.locator('input[type="date"]').first().fill("2000-01-01");
    await page.locator('input[type="date"]').last().fill("2000-01-31");

    await expect(page.getByText(/^0\.00$/).first()).toBeVisible();
  });

  test("office administrator is denied Balance Sheet access", async ({ page }) => {
    await loginAs(page, DEMO_USERS.officeAdmin);
    await page.goto("/reports");
    await expect(page.getByRole("link", { name: /balance sheet/i })).toHaveCount(0);

    await page.goto("/reports/balance-sheet");
    await expect(page.getByText(/don't have permission/i)).toBeVisible();
  });
});
