import { defineConfig, devices } from "@playwright/test";

// Mirrors quickstart.md: expects a docker-composed stack (db + backend +
// frontend, migrated and seeded via `uv run python -m scripts.seed_demo_data`
// and `scripts.seed_bulk_ledger`) already running at these URLs — these
// specs don't start the stack themselves. See T096 in tasks.md.
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
