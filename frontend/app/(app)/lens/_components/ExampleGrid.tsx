"use client";

import { categoryPillClass } from "@/lib/cards/categories";
import { LENS_EXAMPLES } from "@/lib/lens/examples";

import { cn } from "@/lib/utils";

type ExampleGridProps = {
  onSelect: (text: string, sector?: string) => void;
};

export function ExampleGrid({ onSelect }: ExampleGridProps) {
  return (
    <div>
      <h2 className="font-mono text-[10px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
        Example queries
      </h2>
      <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {LENS_EXAMPLES.map((example) => (
          <li key={example.category}>
            <button
              type="button"
              onClick={() => onSelect(example.question, example.category)}
              className="flex h-full w-full flex-col rounded-lg border border-border bg-card p-3 text-left transition-colors hover:border-[#1A4FCC]/40 hover:bg-muted/30"
            >
              <span
                className={cn(
                  "inline-flex w-fit rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold",
                  categoryPillClass(example.category),
                )}
              >
                {example.categoryLabel}
              </span>
              <span className="mt-2 text-[13px] leading-snug text-foreground">
                {example.question}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
