"use client";

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
    <section
      data-testid="dissenting-view"
      className="rounded-[10px] border border-[#FDE68A] bg-[#FFFBEB] p-5"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-amber-300 bg-white px-2 py-0.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-amber-900">
          dissenting view
        </span>
      </div>
      <h3 className="font-display mt-3 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-3 whitespace-pre-wrap text-[13px] leading-relaxed text-slate-700">{body}</p>
    </section>
  );
}
