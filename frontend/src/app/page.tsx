"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { isAuthenticated } from "@/lib/auth";
import { cn } from "@/lib/utils";

const FEATURES = [
  {
    icon: MessageSquareText,
    title: "Talk to your books",
    description:
      '"Add office rent 50000 for July" — the AI assistant creates the record for you, no forms required.',
  },
  {
    icon: BarChart3,
    title: "Live financial reports",
    description:
      "Profit & loss, balance sheet, trial balance, and cash flow — generated instantly from your ledger.",
  },
  {
    icon: ShieldCheck,
    title: "Full audit trail",
    description:
      "Every change, whether made by a person or the AI, is logged and reviewable at any time.",
  },
  {
    icon: Users,
    title: "Built for your team",
    description:
      "Role-based access for business owners, accountants, and office administrators out of the box.",
  },
];

export default function Home() {
  const router = useRouter();
  const [checkedAuth, setCheckedAuth] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    } else {
      setCheckedAuth(true);
    }
  }, [router]);

  if (!checkedAuth) {
    return null;
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-background">
      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-6 animate-in fade-in-0 slide-in-from-top-2 duration-700 fill-mode-both">
        <div className="flex items-center gap-2.5">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <Sparkles className="size-5" />
          </div>
          <span className="text-xl font-bold tracking-tight">FinPilot AI</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            nativeButton={false}
            render={<Link href="/login">Sign in</Link>}
          />
          <Button
            nativeButton={false}
            render={
              <Link href="/register">
                Get Started
                <ArrowRight className="size-4" />
              </Link>
            }
          />
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden">
          {/* Animated gradient blobs */}
          <div className="pointer-events-none absolute inset-0 -z-10">
            <div className="bg-dot-grid absolute inset-0 opacity-[0.4] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,black_10%,transparent_75%)]" />
            <div className="animate-blob absolute -top-24 left-[8%] size-72 rounded-full bg-primary/20 blur-3xl" />
            <div className="animate-blob animate-blob-delay-1 absolute top-10 right-[10%] size-80 rounded-full bg-income/20 blur-3xl" />
            <div className="animate-blob animate-blob-delay-2 absolute top-40 left-[35%] size-64 rounded-full bg-chart-4/20 blur-3xl" />
          </div>

          <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-20 sm:py-28 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
              <div className="mb-6 inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-card px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm animate-in fade-in-0 zoom-in-95 duration-700 delay-100 fill-mode-both">
                <span className="relative flex size-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-income opacity-75" />
                  <span className="relative inline-flex size-1.5 rounded-full bg-income" />
                </span>
                AI-powered accounting assistant
              </div>

              <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl animate-in fade-in-0 slide-in-from-bottom-4 duration-700 delay-150 fill-mode-both">
                Accounting that{" "}
                <span className="bg-gradient-to-r from-primary via-primary to-income bg-clip-text text-transparent">
                  talks back.
                </span>
              </h1>
              <p className="mt-5 max-w-xl text-balance text-lg text-muted-foreground animate-in fade-in-0 slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both">
                Track expenses and income, generate financial reports, and manage your books —
                manually, or by simply asking the AI assistant to do it for you.
              </p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-3 lg:justify-start animate-in fade-in-0 slide-in-from-bottom-4 duration-700 delay-500 fill-mode-both">
                <Button
                  size="lg"
                  nativeButton={false}
                  className="shadow-lg shadow-primary/20 transition-transform hover:scale-[1.03]"
                  render={
                    <Link href="/register">
                      Get Started Free
                      <ArrowRight className="size-4" />
                    </Link>
                  }
                />
                <Button
                  size="lg"
                  variant="outline"
                  nativeButton={false}
                  className="transition-transform hover:scale-[1.03]"
                  render={<Link href="/login">Sign in</Link>}
                />
              </div>
            </div>

            {/* Floating dashboard preview mockup */}
            <div className="relative mx-auto w-full max-w-md animate-in fade-in-0 zoom-in-95 duration-1000 delay-300 fill-mode-both">
              <div className="absolute -inset-4 -z-10 rounded-3xl bg-gradient-to-tr from-primary/10 via-income/10 to-chart-4/10 blur-2xl" />
              <Card className="border-border/60 shadow-2xl">
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">This month</span>
                    <span className="inline-flex items-center gap-1 rounded-md bg-income/10 px-2 py-0.5 text-xs font-medium text-income">
                      <ArrowUpRight className="size-3" />
                      +12.4%
                    </span>
                  </div>
                  <div>
                    <div className="text-3xl font-semibold tracking-tight tabular-nums">
                      $128,450
                    </div>
                    <div className="text-sm text-muted-foreground">Net profit</div>
                  </div>
                  <div className="flex h-20 items-end gap-1.5">
                    {[40, 65, 45, 80, 60, 95, 70, 55, 85, 100, 75, 90].map((h, i) => (
                      <div
                        key={i}
                        className={cn(
                          "flex-1 rounded-sm bg-gradient-to-t from-primary/70 to-primary/30 transition-all duration-700",
                          "animate-in fade-in-0 slide-in-from-bottom fill-mode-both"
                        )}
                        style={{ height: `${h}%`, animationDelay: `${600 + i * 60}ms` }}
                      />
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-3 border-t pt-4">
                    <div>
                      <div className="text-xs text-muted-foreground">Income</div>
                      <div className="text-sm font-semibold text-income">$212,900</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Expenses</div>
                      <div className="text-sm font-semibold text-expense">$84,450</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="absolute -bottom-6 -left-8 hidden w-56 border-border/60 shadow-xl sm:block animate-in fade-in-0 slide-in-from-left-4 duration-700 delay-700 fill-mode-both">
                <CardContent className="flex items-center gap-3 py-3">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Sparkles className="size-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-xs font-medium">&ldquo;Add office rent 5000&rdquo;</div>
                    <div className="text-xs text-muted-foreground">Expense added ✓</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-24">
          <div className="mb-10 text-center">
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Everything your books need
            </h2>
            <p className="mt-2 text-muted-foreground">
              One assistant for expenses, income, reports, and audit history.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((feature, i) => (
              <Card
                key={feature.title}
                className="group border-border/60 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 hover:shadow-lg animate-in fade-in-0 slide-in-from-bottom-4 fill-mode-both"
                style={{ animationDuration: "700ms", animationDelay: `${i * 120}ms` }}
              >
                <CardContent>
                  <div className="mb-3 flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors duration-300 group-hover:bg-primary group-hover:text-primary-foreground">
                    <feature.icon className="size-5" />
                  </div>
                  <h3 className="text-sm font-semibold">{feature.title}</h3>
                  <p className="mt-1.5 text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="relative overflow-hidden border-t">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
          <div className="mx-auto flex max-w-4xl flex-col items-center gap-4 px-6 py-16 text-center">
            <div className="flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <TrendingUp className="size-7" />
            </div>
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Ready to see your business clearly?
            </h2>
            <p className="max-w-md text-muted-foreground">
              Create your account and add your first expense in under a minute.
            </p>
            <Button
              size="lg"
              nativeButton={false}
              className="shadow-lg shadow-primary/20 transition-transform hover:scale-[1.03]"
              render={
                <Link href="/register">
                  Get Started Free
                  <ArrowRight className="size-4" />
                </Link>
              }
            />
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-6 py-8 text-center text-xs text-muted-foreground">
        &copy; {new Date().getFullYear()} FinPilot AI. All rights reserved.
      </footer>
    </div>
  );
}
