"use client";

import type { ReactNode } from "react";
import { useState } from "react";

const TABS = [
  { id: "insight" as const, label: "Insight", tier: 0 },
  { id: "context" as const, label: "Context", tier: 1 },
  { id: "evidence" as const, label: "Evidence", tier: 2 },
];

export type IceTabId = (typeof TABS)[number]["id"];

type IceTabsProps = {
  active: IceTabId;
  onTabChange: (id: IceTabId) => void;
  /** 0 = Insight only; 1 = +Context; 2 = +Evidence (PRD ICE progressive taps). */
  maxUnlockedTier: number;
  onUnlockTier: (tier: 1 | 2) => void;
  panels: Record<IceTabId, ReactNode>;
};

export function IceTabs({
  active,
  onTabChange,
  maxUnlockedTier,
  onUnlockTier,
  panels,
}: IceTabsProps) {
  const [hint, setHint] = useState<string | null>(null);

  function handleSelect(id: IceTabId, tier: number) {
    if (tier === 0) {
      onTabChange("insight");
      setHint(null);
      return;
    }
    if (tier === 1) {
      if (maxUnlockedTier < 1) {
        onUnlockTier(1);
      }
      onTabChange("context");
      setHint(null);
      return;
    }
    if (tier === 2) {
      if (maxUnlockedTier < 1) {
        setHint("Reveal Context first — one tap unlocks the causal chain.");
        return;
      }
      if (maxUnlockedTier < 2) {
        onUnlockTier(2);
      }
      onTabChange("evidence");
      setHint(null);
    }
  }

  return (
    <div>
      <nav className="flex gap-0 border-b border-slate-200" aria-label="ICE layers">
        {TABS.map((t) => {
          const locked = t.tier > maxUnlockedTier;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                handleSelect(t.id, t.tier);
              }}
              className={[
                "-mb-px border-b-2 px-5 py-2.5 font-mono text-[11px] font-semibold uppercase tracking-wide transition-colors",
                active === t.id
                  ? "border-finnwise-blue text-finnwise-blue"
                  : "border-transparent text-slate-500 hover:text-slate-700",
                locked ? "opacity-60" : "",
              ].join(" ")}
            >
              {t.label}
              {locked && t.tier > 0 ? (
                <span className="ml-1 text-[9px] font-normal normal-case text-slate-400">locked</span>
              ) : null}
            </button>
          );
        })}
      </nav>
      {hint ? <p className="mt-2 font-mono text-[10px] text-amber-700">{hint}</p> : null}
      <div className="mt-6">{panels[active]}</div>
    </div>
  );
}
