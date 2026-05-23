import { Skeleton } from "@/components/ui/skeleton";

export default function ThreadLoading() {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden bg-[#F8FAFC]">
      <header className="sticky top-0 z-10 shrink-0 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur md:px-8">
        <div className="flex min-w-0 flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-6 w-40 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
          </div>
          <Skeleton className="h-9 w-44 rounded-lg" />
        </div>
      </header>

      <div className="grid w-full min-w-0 flex-1 grid-cols-1 gap-0 lg:grid-cols-[minmax(0,1fr)_340px]">
        <article className="min-w-0 border-slate-200 px-4 py-8 md:px-10 lg:border-r">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="mt-4 h-9 w-full max-w-2xl" />
          <Skeleton className="mt-3 h-5 w-full max-w-xl" />
          <Skeleton className="mt-8 h-24 w-full rounded-lg" />
          <Skeleton className="mt-10 h-12 w-full max-w-md" />
          <Skeleton className="mt-6 h-64 w-full rounded-lg" />
        </article>

        <aside className="hidden min-w-0 bg-[#F8FAFC] px-6 py-6 lg:block">
          <div className="sticky top-6 min-w-0 space-y-4">
            <Skeleton className="h-36 w-full rounded-lg" />
            <Skeleton className="h-44 w-full rounded-lg" />
            <Skeleton className="h-32 w-full rounded-lg" />
          </div>
        </aside>
      </div>
    </div>
  );
}
