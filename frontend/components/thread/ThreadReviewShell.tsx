import Link from "next/link";
import type { ReactNode } from "react";

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
          <span className="rounded-full bg-violet-100 px-2.5 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide text-violet-800">
            {categoryLabel.replaceAll("_", " ")}
          </span>
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide text-slate-600">
            {lifecycleLabel}
          </span>
        </div>
      </header>

      <div className="grid flex-1 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="border-r border-slate-200 bg-white">{children}</div>
        <aside className="bg-finnwise-surface p-6 lg:min-h-[calc(100vh-52px)]">{aside}</aside>
      </div>
    </div>
  );
}
