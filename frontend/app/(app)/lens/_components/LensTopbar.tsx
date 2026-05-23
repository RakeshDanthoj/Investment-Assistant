import { PhaseBadge } from "./PhaseBadge";

export function LensTopbar() {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background">
      <div className="mx-auto flex max-w-[680px] items-start justify-between gap-3 px-4 py-3">
        <div className="min-w-0">
          <h1 className="font-display text-xl font-semibold text-foreground">The Lens</h1>
          <p className="text-[13px] text-muted-foreground">
            Ask about any event. Get the full causal chain in 30–90 seconds.
          </p>
        </div>
        <PhaseBadge />
      </div>
    </header>
  );
}
