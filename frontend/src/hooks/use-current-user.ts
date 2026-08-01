"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import { isAuthenticated, type AuthUser } from "@/lib/auth";

export function useCurrentUser() {
  return useQuery<AuthUser>({
    queryKey: ["auth", "me"],
    queryFn: () => apiFetch<AuthUser>("/auth/me"),
    enabled: isAuthenticated(),
    retry: false,
  });
}
