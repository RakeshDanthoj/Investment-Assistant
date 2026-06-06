"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { SIDEBAR_NAV_ITEMS } from "./Sidebar";

export function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-card min-[860px]:hidden"
      aria-label="Primary"
    >
      <ul className="mx-auto flex max-w-lg items-stretch justify-around px-1 py-1">
        {SIDEBAR_NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const shortLabel = item.label.replace(/^The /, "");
          return (
            <li key={item.href} className="min-w-0 flex-1">
              <Button
                variant="ghost"
                size="sm"
                asChild
                className={cn(
                  "h-auto w-full flex-col gap-0.5 px-1 py-1.5 text-[10px] font-normal",
                  isActive && "bg-secondary text-secondary-foreground hover:bg-secondary",
                )}
              >
                <Link href={item.href}>
                  <span className="truncate">{shortLabel}</span>
                </Link>
              </Button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
