"use client";

import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import { clearTokens, getRefreshToken } from "@/lib/auth";

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return async function logout() {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) {
        await apiFetch("/auth/logout", {
          method: "POST",
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch {
      // Best-effort server-side revocation; proceed with local logout regardless.
    } finally {
      clearTokens();
      queryClient.clear();
      router.push("/login");
    }
  };
}
