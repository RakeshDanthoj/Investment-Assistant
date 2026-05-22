"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NotificationBadge } from "@/components/Topbar/NotificationBadge";
import { PhaseBadge } from "@/components/Topbar/PhaseBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

import UserChipContainer from "./UserChipContainer";

export type SidebarNavItem = {
  href: string;
  label: string;
  phase2?: boolean;
};

export const SIDEBAR_NAV_ITEMS: readonly SidebarNavItem[] = [
  { href: "/pulse", label: "The Pulse" },
  { href: "/thread", label: "The Thread" },
  { href: "/mirror", label: "The Mirror", phase2: true },
  { href: "/lens", label: "The Lens", phase2: true },
  { href: "/map", label: "The Map" },
] as const;

type SidebarProps = {
  userName: string;
  userEmail: string;
};

export default function Sidebar({ userName, userEmail }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="flex h-svh w-[220px] shrink-0 flex-col border-r border-border bg-sidebar">
      <div className="p-6">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-display text-[18px] font-bold leading-tight text-sidebar-foreground">
              FinnWise
            </p>
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">
              Event intelligence
            </p>
          </div>
          <div className="flex items-center gap-2">
            <PhaseBadge />
            <NotificationBadge />
          </div>
        </div>
      </div>
      <Separator />
      <nav className="flex-1 px-2.5 py-4">
        <p className="px-2 font-mono text-[9px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
          Surfaces
        </p>
        <ul className="mt-2 space-y-0.5">
          {SIDEBAR_NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.href}>
                <Button
                  variant="ghost"
                  asChild
                  className={cn(
                    "h-9 w-full justify-start gap-2.5 px-2.5 text-[13px] font-normal",
                    isActive &&
                      "bg-sidebar-accent font-medium text-sidebar-accent-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Link href={item.href}>
                    <span className="min-w-0 flex-1">{item.label}</span>
                    {item.phase2 ? (
                      <Badge variant="phase2" className="ml-auto shrink-0 px-1.5 py-0.5 text-[9px]">
                        Phase 2
                      </Badge>
                    ) : null}
                  </Link>
                </Button>
              </li>
            );
          })}
        </ul>
      </nav>
      <UserChipContainer userName={userName} userEmail={userEmail} />
    </aside>
  );
}
