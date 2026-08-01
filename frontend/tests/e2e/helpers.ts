import type { Page } from "@playwright/test";

// Matches backend/scripts/seed_demo_data.py
export const DEMO_USERS = {
  owner: { email: "owner@finpilot.demo", password: "DemoPass123!" },
  accountant: { email: "accountant@finpilot.demo", password: "DemoPass123!" },
  officeAdmin: { email: "admin@finpilot.demo", password: "DemoPass123!" },
};

export async function loginAs(page: Page, user: { email: string; password: string }) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(user.email);
  await page.getByLabel(/password/i).fill(user.password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/dashboard");
}
