import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §4 (spec.md User Story 3). Requires a configured,
// reachable AI_PROVIDER on the backend — without one, the assistant reports
// itself unavailable and these assertions won't be reached (see
// us-ai-unavailable.spec.ts for that path instead).
test.describe("US3 - Conversational AI Data Entry", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, DEMO_USERS.accountant);
    await page.goto("/ai-assistant");
  });

  test("proposes an expense and only creates it after confirmation", async ({ page }) => {
    await page.getByPlaceholder(/ask finpilot/i).fill("Add office rent 50000 for July");
    await page.getByRole("button", { name: /send/i }).click();

    await expect(page.getByText(/add expense: office rent/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("button", { name: /^confirm$/i })).toBeVisible();

    await page.getByRole("button", { name: /^confirm$/i }).click();
    await expect(page.getByText(/added expense 'office rent'/i)).toBeVisible();

    await page.goto("/expenses");
    await expect(page.getByRole("row", { name: /office rent/i })).toBeVisible();
  });

  test("asks a clarifying question instead of guessing when the amount is missing", async ({ page }) => {
    await page.getByPlaceholder(/ask finpilot/i).fill("Add an expense");
    await page.getByRole("button", { name: /send/i }).click();

    await expect(page.getByText(/\?/)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("button", { name: /^confirm$/i })).toHaveCount(0);
  });
});
