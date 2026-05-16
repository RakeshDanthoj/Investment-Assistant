"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import UserChipContainer from "./UserChipContainer";

const NAV_ITEMS = [
  { href: "/pulse", label: "The Pulse" },
  { href: "/thread", label: "The Thread" },
  { href: "/mirror", label: "The Mirror" },
  { href: "/lens", label: "The Lens" },
  { href: "/map", label: "The Map" },
] as const;

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
    <div className="flex min-h-screen">
      <aside className="flex w-[220px] shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4">
          <p className="font-display text-lg font-bold text-slate-900">
            FinnWise
          </p>
          <p className="font-mono text-[9px] uppercase tracking-wider text-slate-400">
            Event intelligence
          </p>
        </div>
        <nav className="flex-1 px-3 py-4">
          <p className="px-2 font-mono text-[9px] uppercase tracking-wider text-slate-400">
            Surfaces
          </p>
          <ul className="mt-2 space-y-0.5">
            {NAV_ITEMS.map((item) => {
              const isActive =
                pathname === item.href ||
                pathname.startsWith(`${item.href}/`);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`block rounded-md px-2 py-2 text-sm ${
                      isActive
                        ? "bg-finnwise-blue-tint font-medium text-finnwise-blue"
                        : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <UserChipContainer userName={userName} userEmail={userEmail} />
      </aside>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
