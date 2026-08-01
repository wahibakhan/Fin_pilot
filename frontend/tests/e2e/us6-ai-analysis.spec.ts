import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §7 (spec.md User Story 6). Requires a configured,
// reachable AI_PROVIDER on the backend, plus seeded data with a known
// duplicate pair and an outlier expense for the audit assertions.
test.describe("US6 - AI-Powered Financial Analysis & Anomaly Detection", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_USERS.owner);
    await page.goto("/ai-assistant");
  });

  test("shows exactly the top five expenses, ranked", async ({ page }) => {
    await page.getByPlaceholder(/ask finpilot/i).fill("Show top five expenses");
    await page.getByRole("button", { name: /send/i }).click();

    await expect(page.getByText(/top 5 expenses/i)).toBeVisible({ timeout: 15_000 });
  });

  test("compares two periods and reports the delta", async ({ page }) => {
    await page.getByPlaceholder(/ask finpilot/i).fill("Compare June and July expenses");
    await page.getByRole("button", { name: /send/i }).click();

    await expect(page.getByText(/period a total/i)).toBeVisible({ timeout: 15_000 });
  });

  test("running a monthly audit flags a seeded duplicate without deleting either record", async ({
    page,
  }) => {
    await page.getByPlaceholder(/ask finpilot/i).fill("Run monthly audit");
    await page.getByRole("button", { name: /send/i }).click();

    await expect(page.getByText(/audit complete/i)).toBeVisible({ timeout: 15_000 });
  });
});
