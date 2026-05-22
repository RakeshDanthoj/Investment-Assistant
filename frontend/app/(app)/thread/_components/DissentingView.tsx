"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

function splitTitleBody(raw: string): { title: string; body: string } {
  const t = raw.trim();
  if (!t) return { title: "Dissenting view", body: "" };
  const parts = t.split(/\n\n+/);
  const title = parts[0]?.slice(0, 160) ?? "Dissenting view";
  const body = parts.slice(1).join("\n\n").trim() || parts[0]?.slice(160).trim() || "";
  return { title, body: body || parts[0] || "" };
}

type DissentingViewProps = {
  text: string;
};

export function DissentingView({ text }: DissentingViewProps) {
  const { title, body } = splitTitleBody(text);

  return (
    <Card
      data-testid="dissenting-view"
      className="w-full min-w-0 rounded-[10px] border-[#FDE68A] bg-[#FFFBEB] py-0 shadow-none ring-[#FDE68A]"
    >
      <CardContent className="p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className="rounded-full border-amber-300 bg-white font-mono text-[9px] font-semibold uppercase tracking-wide text-amber-900"
          >
            dissenting view
          </Badge>
        </div>
        <h3 className="font-display mt-3 text-base font-semibold text-slate-900">{title}</h3>
        <p className="mt-3 text-[13px] leading-relaxed whitespace-pre-wrap text-slate-700">{body}</p>
      </CardContent>
    </Card>
  );
}
