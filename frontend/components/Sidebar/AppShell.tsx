"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { SebiFooter } from "@/components/SebiFooter";
import { PhaseBadge } from "@/components/Topbar/PhaseBadge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import Sidebar, { SIDEBAR_NAV_ITEMS } from "./Sidebar";

const NotificationBadge = dynamic(
  () =>
    import("@/components/Topbar/NotificationBadge").then((m) => ({
      default: m.NotificationBadge,
    })),
  { ssr: false },
);

type AppShellProps = {
  children: ReactNode;
  userName: string;
  userEmail: string;
};

export default function AppShell({
  children,
  userName,
  userEmail,
}: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-svh flex-col overflow-hidden bg-background">
      <div className="fixed inset-y-0 left-0 z-30 hidden min-[860px]:block">
        <Sidebar userName={userName} userEmail={userEmail} />
      </div>

      <header className="z-20 flex shrink-0 items-center gap-2 border-b border-border bg-card px-3 py-2 min-[860px]:hidden">
        <div className="shrink-0">
          <p className="font-display text-base font-bold text-foreground">FinnWise</p>
        </div>
        <nav
          className="flex min-w-0 flex-1 gap-1 overflow-x-auto py-1"
          aria-label="Primary"
        >
          {SIDEBAR_NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Button
                key={item.href}
                variant="ghost"
                size="sm"
                asChild
                className={cn(
                  "shrink-0 text-xs",
                  isActive && "bg-secondary font-medium text-secondary-foreground hover:bg-secondary",
                )}
              >
                <Link href={item.href}>
                  {item.label.replace(/^The /, "")}
                  {item.phase2 ? " · P2" : ""}
                </Link>
              </Button>
            );
          })}
        </nav>
        <div className="flex shrink-0 items-center gap-2">
          <PhaseBadge />
          <NotificationBadge />
        </div>
      </header>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden min-[860px]:pl-[220px]">
        <div className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto overscroll-y-contain">
          {children}
        </div>
        <SebiFooter />
      </div>
    </div>
  );
}
