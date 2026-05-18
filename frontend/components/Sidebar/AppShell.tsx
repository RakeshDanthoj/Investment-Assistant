"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { SebiFooter } from "@/components/SebiFooter";
import { NotificationBadge } from "@/components/Topbar/NotificationBadge";

import Sidebar, { SIDEBAR_NAV_ITEMS } from "./Sidebar";

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
    <div className="flex min-h-screen flex-col bg-finnwise-surface min-[860px]:flex-row">
      <div className="hidden min-[860px]:block">
        <Sidebar userName={userName} userEmail={userEmail} />
      </div>

      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2 min-[860px]:hidden">
        <div className="shrink-0">
          <p className="font-display text-base font-bold text-slate-900">FinnWise</p>
        </div>
        <nav
          className="flex min-w-0 flex-1 gap-1 overflow-x-auto py-1"
          aria-label="Primary"
        >
          {SIDEBAR_NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`shrink-0 rounded-md px-2 py-1.5 text-xs transition-all duration-150 ease-in-out ${
                  isActive
                    ? "bg-finnwise-blue-tint font-medium text-finnwise-blue"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {item.label.replace(/^The /, "")}
                {item.phase2 ? " · P2" : ""}
              </Link>
            );
          })}
        </nav>
        <NotificationBadge />
      </header>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</div>
        <SebiFooter />
      </div>
    </div>
  );
}
