"use client";

import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { SebiFooter } from "@/components/SebiFooter";
import type { EditorialNavAccess } from "@/lib/admin-nav";

import { MobileBottomNav } from "./MobileBottomNav";
import Sidebar from "./Sidebar";

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
  editorialAccess: EditorialNavAccess;
};

export default function AppShell({
  children,
  userName,
  userEmail,
  editorialAccess,
}: AppShellProps) {
  const pathname = usePathname();
  const showSignalNotificationBadge = !pathname.startsWith("/mirror");
  const deferNotificationUntilFeed = pathname.startsWith("/pulse");

  return (
    <div className="flex h-svh flex-col overflow-hidden bg-background">
      <div className="fixed inset-y-0 left-0 z-30 hidden min-[860px]:block">
        <Sidebar
          userName={userName}
          userEmail={userEmail}
          editorialAccess={editorialAccess}
        />
      </div>

      <header className="z-20 flex shrink-0 items-center justify-between gap-2 border-b border-border bg-card px-3 py-2 min-[860px]:hidden">
        <p className="font-display text-base font-bold text-foreground">FinnWise</p>
        {showSignalNotificationBadge ? (
          <NotificationBadge deferUntilFeedReady={deferNotificationUntilFeed} />
        ) : null}
      </header>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden min-[860px]:pl-[220px]">
        <div className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto overscroll-y-contain pb-14 min-[860px]:pb-0">
          {children}
        </div>
        <SebiFooter />
      </div>

      <MobileBottomNav />
    </div>
  );
}
