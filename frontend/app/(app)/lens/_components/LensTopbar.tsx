export function LensTopbar() {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background">
      <div className="mx-auto max-w-[680px] px-4 py-3">
        <h1 className="font-display text-xl font-semibold text-foreground">The Lens</h1>
        <p className="text-[13px] text-muted-foreground">
          Ask about any event. Get the full causal chain in 30–90 seconds.
        </p>
      </div>
    </header>
  );
}
