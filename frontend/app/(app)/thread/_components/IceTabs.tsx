"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

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
    <Tabs
      value={active}
      className="w-full min-w-0"
      onValueChange={(value) => {
        const tab = TABS.find((t) => t.id === value);
        if (tab) handleSelect(tab.id, tab.tier);
      }}
    >
      <TabsList
        variant="line"
        aria-label="ICE layers"
        className="h-auto w-full justify-start gap-0 rounded-none border-b border-slate-200 bg-transparent p-0"
      >
        {TABS.map((t) => {
          const locked = t.tier > maxUnlockedTier;
          return (
            <TabsTrigger
              key={t.id}
              value={t.id}
              className={cn(
                "-mb-px flex-none rounded-none border-b-2 border-transparent px-5 py-2.5 font-mono text-[11px] font-semibold uppercase tracking-wide shadow-none after:hidden data-[state=active]:border-finnwise-blue data-[state=active]:bg-transparent data-[state=active]:text-finnwise-blue data-[state=active]:shadow-none",
                locked ? "opacity-60" : "text-slate-500 hover:text-slate-700",
              )}
            >
              {t.label}
              {locked && t.tier > 0 ? (
                <span className="ml-1 text-[9px] font-normal normal-case text-slate-400">locked</span>
              ) : null}
            </TabsTrigger>
          );
        })}
      </TabsList>
      {hint ? <p className="mt-2 font-mono text-[10px] text-amber-700">{hint}</p> : null}
      {TABS.map((t) => (
        <TabsContent key={t.id} value={t.id} className="mt-6 w-full min-w-0 outline-none">
          {panels[t.id]}
        </TabsContent>
      ))}
    </Tabs>
  );
}
