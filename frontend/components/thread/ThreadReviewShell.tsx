import Link from "next/link";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";

type ThreadReviewShellProps = {
  categoryLabel: string;
  lifecycleLabel: string;
  aside: ReactNode;
  children: ReactNode;
};

export default function ThreadReviewShell({
  categoryLabel,
  lifecycleLabel,
  aside,
  children,
}: ThreadReviewShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-finnwise-surface">
      <header className="sticky top-0 z-10 flex h-[52px] items-center justify-between border-b border-slate-200 bg-white px-6">
        <Link
          href="/admin/queue"
          className="text-sm font-medium text-finnwise-blue hover:opacity-80"
        >
          ← Editorial queue
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="phase2"
            className="rounded-full px-2.5 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide"
          >
            {categoryLabel.replaceAll("_", " ")}
          </Badge>
          <Badge
            variant="secondary"
            className="rounded-full px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide text-slate-600"
          >
            {lifecycleLabel}
          </Badge>
        </div>
      </header>

      <div className="grid flex-1 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="border-r border-slate-200 bg-white">{children}</div>
        <aside className="bg-finnwise-surface p-6 lg:min-h-[calc(100vh-52px)]">{aside}</aside>
      </div>
    </div>
  );
}
