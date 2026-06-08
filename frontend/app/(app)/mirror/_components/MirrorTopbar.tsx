import { FilterPills } from "./FilterPills";

type MirrorTopbarProps = {
  status: string | null;
  showFilters?: boolean;
  onStatusChange?: (next: string | null) => void;
  notificationSlot?: React.ReactNode;
};

export function MirrorTopbar({
  status,
  showFilters = true,
  onStatusChange,
  notificationSlot,
}: MirrorTopbarProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 min-[860px]:flex-row min-[860px]:items-start min-[860px]:justify-between">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <h1 className="font-display text-xl font-semibold text-foreground">The Mirror</h1>
              <p className="text-[13px] text-muted-foreground">
                Not what your portfolio is worth. What your reasoning was worth.
              </p>
            </div>
            {notificationSlot ? (
              <div className="ml-auto shrink-0" data-testid="mirror-notification-slot">
                {notificationSlot}
              </div>
            ) : null}
          </div>
          {showFilters && onStatusChange ? (
            <FilterPills status={status} onStatusChange={onStatusChange} />
          ) : null}
        </div>
      </div>
    </header>
  );
}
