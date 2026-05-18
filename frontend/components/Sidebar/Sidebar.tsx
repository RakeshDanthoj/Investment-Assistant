"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NotificationBadge } from "@/components/Topbar/NotificationBadge";

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
    <aside className="flex h-full w-[220px] shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-6">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-display text-[18px] font-bold leading-tight text-slate-900">
              FinnWise
            </p>
            <p className="mt-1 font-mono text-[10px] text-slate-400">
              Event intelligence
            </p>
          </div>
          <NotificationBadge />
        </div>
      </div>
      <nav className="flex-1 px-2.5 py-4">
        <p className="px-2 font-mono text-[9px] font-medium uppercase tracking-[0.06em] text-slate-400">
          Surfaces
        </p>
        <ul className="mt-2 space-y-0.5">
          {SIDEBAR_NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex min-h-[36px] items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] transition-all duration-150 ease-in-out ${
                    isActive
                      ? "bg-finnwise-blue-tint font-medium text-finnwise-blue"
                      : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <span className="min-w-0 flex-1">{item.label}</span>
                  {item.phase2 ? (
                    <span className="ml-auto shrink-0 rounded px-1.5 py-0.5 font-mono text-[9px] text-[#6B21A8] bg-[#F3E8FF]">
                      Phase 2
                    </span>
                  ) : null}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <UserChipContainer userName={userName} userEmail={userEmail} />
    </aside>
  );
}
