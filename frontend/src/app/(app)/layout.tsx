"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { isAuthenticated } from "@/lib/auth";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      setAuthorized(true);
    } else {
      router.replace("/login");
    }
  }, [router]);

  // Render nothing until we've confirmed a session exists, so no protected
  // content or data-fetching child ever mounts for an unauthenticated visitor.
  if (!authorized) {
    return null;
  }

  return <AppShell>{children}</AppShell>;
}
