import { describe, expect, it } from "vitest";

import { can, visibleNavItems } from "@/lib/rbac";

describe("rbac", () => {
  it("grants business_owner every permission", () => {
    expect(can("business_owner", "expenses:delete")).toBe(true);
    expect(can("business_owner", "audit-log:view")).toBe(true);
    expect(can("business_owner", "reports:balance-sheet")).toBe(true);
    expect(can("business_owner", "users:manage")).toBe(true);
  });

  it("grants accountant everything except user management", () => {
    expect(can("accountant", "expenses:delete")).toBe(true);
    expect(can("accountant", "audit-log:view")).toBe(true);
    expect(can("accountant", "reports:balance-sheet")).toBe(true);
    expect(can("accountant", "users:manage")).toBe(false);
  });

  it("denies office_administrator delete, audit log, and sensitive reports", () => {
    expect(can("office_administrator", "expenses:delete")).toBe(false);
    expect(can("office_administrator", "income:delete")).toBe(false);
    expect(can("office_administrator", "audit-log:view")).toBe(false);
    expect(can("office_administrator", "reports:balance-sheet")).toBe(false);
    expect(can("office_administrator", "reports:trial-balance")).toBe(false);
  });

  it("hides the audit log nav item for office_administrator", () => {
    const items = visibleNavItems("office_administrator");
    expect(items.some((item) => item.href === "/audit-log")).toBe(false);
  });

  it("shows the audit log nav item for business_owner and accountant", () => {
    expect(visibleNavItems("business_owner").some((i) => i.href === "/audit-log")).toBe(true);
    expect(visibleNavItems("accountant").some((i) => i.href === "/audit-log")).toBe(true);
  });
});
