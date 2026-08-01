import {
  LayoutDashboard,
  Receipt,
  Wallet,
  BookOpenText,
  FileBarChart2,
  Sparkles,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import type { UserRole } from "@/lib/auth";

/**
 * Mirrors the FR-003 permission matrix from spec.md. This is a UX convenience
 * (hide/disable affordances a user isn't allowed to use) — the backend is the
 * real enforcement point, this must never be relied on for security.
 */
export type Action =
  | "expenses:delete"
  | "income:delete"
  | "reports:balance-sheet"
  | "reports:trial-balance"
  | "audit-log:view"
  | "users:manage";

const ROLE_ACTIONS: Record<UserRole, Set<Action>> = {
  business_owner: new Set<Action>([
    "expenses:delete",
    "income:delete",
    "reports:balance-sheet",
    "reports:trial-balance",
    "audit-log:view",
    "users:manage",
  ]),
  accountant: new Set<Action>([
    "expenses:delete",
    "income:delete",
    "reports:balance-sheet",
    "reports:trial-balance",
    "audit-log:view",
  ]),
  office_administrator: new Set<Action>([]),
};

export function can(role: UserRole, action: Action): boolean {
  return ROLE_ACTIONS[role]?.has(action) ?? false;
}

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  requires?: Action;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Expenses", href: "/expenses", icon: Receipt },
  { label: "Income", href: "/income", icon: Wallet },
  { label: "Ledger", href: "/ledger", icon: BookOpenText },
  { label: "Reports", href: "/reports", icon: FileBarChart2 },
  { label: "AI Assistant", href: "/ai-assistant", icon: Sparkles },
  { label: "Audit Log", href: "/audit-log", icon: ShieldCheck, requires: "audit-log:view" },
];

export function visibleNavItems(role: UserRole): NavItem[] {
  return NAV_ITEMS.filter((item) => !item.requires || can(role, item.requires));
}
