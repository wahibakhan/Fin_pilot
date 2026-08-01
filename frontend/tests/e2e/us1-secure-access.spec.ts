import { expect, test } from "@playwright/test";

import { DEMO_USERS, loginAs } from "./helpers";

// Mirrors quickstart.md §2 (spec.md User Story 1).
test.describe("US1 - Secure Role-Based Access", () => {
  test("unauthenticated visitors are redirected to login with no data revealed", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForURL("**/login");
    await expect(page.getByRole("heading", { name: /finpilot ai/i })).toBeVisible();
  });

  test("invalid credentials show an error and grant no access", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("nobody@finpilot.demo");
    await page.getByLabel(/password/i).fill("wrong-password");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("business owner sees full nav including audit log", async ({ page }) => {
    await loginAs(page, DEMO_USERS.owner);
    await expect(page.getByRole("link", { name: "Audit Log" })).toBeVisible();
  });

  test("office administrator does not see the audit log link, and cannot open it directly", async ({
    page,
  }) => {
    await loginAs(page, DEMO_USERS.officeAdmin);
    await expect(page.getByRole("link", { name: "Audit Log" })).toHaveCount(0);

    await page.goto("/audit-log");
    await expect(page.getByText(/don't have permission/i)).toBeVisible();
  });

  test("logout invalidates the session so protected pages redirect again", async ({ page }) => {
    await loginAs(page, DEMO_USERS.owner);
    await page.getByRole("button", { name: /olivia owner/i }).click();
    await page.getByText(/log out/i).click();
    await page.waitForURL("**/login");

    await page.goto("/dashboard");
    await page.waitForURL("**/login");
  });
});
