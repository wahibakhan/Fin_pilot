import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §8 (SC-008). Requires the backend to be started with
// an invalid/unset AI provider key for this run specifically — a separate
// backend configuration from the other e2e specs, hence its own file rather
// than folded into one of the six user-story specs.
test.describe("AI-unavailable graceful degradation (SC-008)", () => {
  test("chat panel shows the unavailable state instead of crashing", async ({ page }) => {
    await loginAs(page, DEMO_USERS.owner);
    await page.goto("/ai-assistant");

    await page.getByPlaceholder(/ask finpilot/i).fill("Add office rent 50000 for July");
    await page.getByRole("button", { name: /send/i }).click();

    await expect(page.getByText(/ai assistant unavailable/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByPlaceholder(/ask finpilot/i)).toBeDisabled();
  });

  test("manual expense/income/reports/ledger flows are entirely unaffected", async ({ page }) => {
    await loginAs(page, DEMO_USERS.accountant);

    await page.goto("/expenses");
    await expect(page.getByRole("button", { name: /add expense/i })).toBeEnabled();

    await page.goto("/income");
    await expect(page.getByRole("button", { name: /add income/i })).toBeEnabled();

    await page.goto("/ledger");
    await expect(page.getByRole("table")).toBeVisible();

    await page.goto("/reports/profit-and-loss");
    await expect(page.getByText("Net Profit")).toBeVisible();
  });
});
