"use client";

import { useLayoutEffect, useRef, type ReactNode } from "react";

type PulseStickyHeaderProps = {
  children: ReactNode;
};

/** Sticky Pulse chrome; publishes `--pulse-sticky-header-height` for InsightPanel offset. */
export function PulseStickyHeader({ children }: PulseStickyHeaderProps) {
  const ref = useRef<HTMLElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;

    const root = document.documentElement;
    const syncHeight = () => {
      root.style.setProperty("--pulse-sticky-header-height", `${el.offsetHeight}px`);
    };

    syncHeight();
    const observer = new ResizeObserver(syncHeight);
    observer.observe(el);

    return () => {
      observer.disconnect();
      root.style.removeProperty("--pulse-sticky-header-height");
    };
  }, []);

  return (
    <header
      ref={ref}
      className="sticky top-0 z-10 shrink-0 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80"
    >
      {children}
    </header>
  );
}
