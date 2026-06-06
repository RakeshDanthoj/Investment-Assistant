"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { EditorialNavAccess } from "@/lib/admin-nav";
import { cn } from "@/lib/utils";

type EditorialNavProps = {
  pathname: string;
  access: EditorialNavAccess;
};

const EDITORIAL_LINKS = [
  { href: "/admin/queue", label: "Editorial queue", flag: "showEditorQueue" },
  { href: "/admin/signal-queue", label: "Signal queue", flag: "showSignalQueue" },
  { href: "/editor/watchlist", label: "Watchlist", flag: "showWatchlist" },
  { href: "/admin/factor-db", label: "Factor DB", flag: "showFactorDb" },
] as const satisfies ReadonlyArray<{
  href: string;
  label: string;
  flag: keyof EditorialNavAccess;
}>;

export function EditorialNav({ pathname, access }: EditorialNavProps) {
  if (!access.showEditorialSection) return null;

  const links = EDITORIAL_LINKS.filter((item) => access[item.flag]);

  if (links.length === 0) return null;

  return (
    <div className="mt-6 px-2">
      <p className="px-2 font-mono text-[9px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
        Editorial
      </p>
      <ul className="mt-2 space-y-0.5">
        {links.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <li key={item.href}>
              <Button
                variant="ghost"
                asChild
                className={cn(
                  "h-9 w-full justify-start px-2.5 text-[13px] font-normal",
                  isActive &&
                    "bg-sidebar-accent font-medium text-sidebar-accent-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                )}
              >
                <Link href={item.href}>{item.label}</Link>
              </Button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
