"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export type InstrumentAssessmentRow = {
  instrument_id: string;
  signal_type: string;
  reasoning: string | null;
  entry_conditions: string[];
  exit_conditions: string[];
};

export type IceCardReaderProps = {
  title: string;
  eventTitle: string;
  eventConfidenceScore: number;
  insightLayer: string;
  contextLayer: string;
  evidenceLayer: Record<string, unknown>;
  dissentingView: string;
  frameworkBehindThis: string;
  instrumentAssessments: InstrumentAssessmentRow[];
};

const ICE_TABS = [
  { id: "insight", label: "Insight" },
  { id: "context", label: "Context" },
  { id: "evidence", label: "Evidence" },
] as const;

type IceTabId = (typeof ICE_TABS)[number]["id"];

function confidenceDots(score: number): { direction: string; magnitude: string } {
  if (score >= 70) return { direction: "Higher confidence", magnitude: "Higher confidence" };
  if (score >= 40) return { direction: "Moderate confidence", magnitude: "Moderate confidence" };
  return { direction: "Limited confidence", magnitude: "Limited confidence" };
}

function signalBadgeClass(signalType: string): string {
  if (signalType === "positive") return "bg-emerald-50 text-finnwise-green";
  if (signalType === "negative") return "bg-red-50 text-finnwise-red";
  return "bg-amber-50 text-finnwise-amber";
}

export default function IceCardReader({
  title,
  eventTitle,
  eventConfidenceScore,
  insightLayer,
  contextLayer,
  evidenceLayer,
  dissentingView,
  frameworkBehindThis,
  instrumentAssessments,
}: IceCardReaderProps) {
  const [tab, setTab] = useState<IceTabId>("insight");
  const dots = useMemo(() => confidenceDots(eventConfidenceScore), [eventConfidenceScore]);

  const evidenceMarkdown =
    typeof evidenceLayer.markdown === "string" ? evidenceLayer.markdown : "";
  const macroStub =
    typeof evidenceLayer.macro_stub === "string" ? evidenceLayer.macro_stub : "";

  return (
    <article className="max-w-3xl px-8 py-10 pb-16">
      <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
        Event Intelligence Card · read-only
      </p>
      <h1 className="font-display mt-2 text-[26px] leading-snug font-semibold text-slate-900">
        {title}
      </h1>
      <p className="mt-3 text-[15px] leading-relaxed font-light italic text-slate-600">
        {eventTitle}
      </p>

      <Card className="mt-8 overflow-hidden rounded-lg py-0 shadow-none ring-slate-200">
        <CardContent className="flex gap-0 p-0">
          <div className="flex-1 border-r border-slate-200 bg-white px-4 py-3">
            <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
              Direction confidence
            </p>
            <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
              <span className="h-2 w-2 rounded-full bg-finnwise-blue" aria-hidden />
              {dots.direction}
            </p>
          </div>
          <div className="flex-1 bg-white px-4 py-3">
            <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
              Magnitude confidence
            </p>
            <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
              <span className="h-2 w-2 rounded-full bg-amber-400" aria-hidden />
              {dots.magnitude}{" "}
              <span className="font-normal text-slate-400">({eventConfidenceScore}/100)</span>
            </p>
          </div>
        </CardContent>
      </Card>

      <Tabs value={tab} onValueChange={(value) => setTab(value as IceTabId)} className="mt-8">
        <TabsList
          variant="line"
          className="h-auto w-full justify-start gap-0 rounded-none border-b border-slate-200 bg-transparent p-0"
        >
          {ICE_TABS.map((t) => (
            <TabsTrigger
              key={t.id}
              value={t.id}
              className="-mb-px flex-none rounded-none border-b-2 border-transparent px-5 py-2.5 text-[13px] font-medium shadow-none after:hidden data-[state=active]:border-finnwise-blue data-[state=active]:bg-transparent data-[state=active]:text-finnwise-blue data-[state=active]:shadow-none"
            >
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <Card className="mt-7 rounded-[10px] py-0 shadow-none ring-slate-200">
          <CardContent className="p-6">
            <TabsContent value="insight" className="mt-0">
              <ProseBlock text={insightLayer} />
            </TabsContent>
            <TabsContent value="context" className="mt-0">
              <ProseBlock text={contextLayer} />
            </TabsContent>
            <TabsContent value="evidence" className="mt-0">
              <div className="space-y-4">
                <ProseBlock text={evidenceMarkdown} />
                {macroStub ? (
                  <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-[12px] leading-relaxed text-slate-600">
                    {macroStub}
                  </p>
                ) : null}
              </div>
            </TabsContent>
          </CardContent>
        </Card>
      </Tabs>

      {instrumentAssessments.length ? (
        <section className="mt-10">
          <h2 className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
            Instrument assessments
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {instrumentAssessments.map((row) => (
              <Card
                key={`${row.instrument_id}-${row.signal_type}`}
                className="rounded-[10px] py-0 shadow-none ring-slate-200"
                size="sm"
              >
                <CardContent className="p-4">
                  <p className="text-sm font-semibold text-slate-900">{row.instrument_id}</p>
                  <Badge
                    variant="outline"
                    className={`mt-2 rounded-full px-2 py-0.5 font-mono text-[11px] font-medium ${signalBadgeClass(row.signal_type)}`}
                  >
                    {row.signal_type}
                  </Badge>
                  {row.reasoning ? (
                    <p className="mt-3 text-[12px] leading-relaxed text-slate-600">{row.reasoning}</p>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      <Card className="mt-10 rounded-[10px] border-slate-300 bg-slate-50 py-0 shadow-none ring-slate-300">
        <CardContent className="p-6">
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="rounded-full border-slate-300 font-mono text-[10px] uppercase tracking-wide text-slate-500"
            >
              Dissent
            </Badge>
            <h2 className="font-display text-sm font-semibold text-slate-900">
              Mechanistic counter-view
            </h2>
          </div>
          <ProseBlock text={dissentingView} className="mt-4 border-0 bg-transparent p-0" />
        </CardContent>
      </Card>

      <section className="mt-8 rounded-[10px] border border-finnwise-blue-tint bg-gradient-to-br from-[#EBF0FD] to-emerald-50 p-6">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-finnwise-blue">
          Framework behind this
        </p>
        <ProseBlock
          text={frameworkBehindThis}
          className="mt-3 border-0 bg-transparent p-0 text-[13px]"
        />
      </section>
    </article>
  );
}

function ProseBlock({ text, className = "" }: { text: string; className?: string }) {
  return (
    <div
      className={`text-[15px] leading-relaxed font-light whitespace-pre-wrap text-slate-700 ${className}`}
    >
      {text || "—"}
    </div>
  );
}
