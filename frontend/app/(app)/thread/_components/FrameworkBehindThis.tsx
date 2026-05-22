"use client";

type FrameworkBehindThisProps = {
  text: string;
};

export function FrameworkBehindThis({ text }: FrameworkBehindThisProps) {
  const body = text.trim() || "—";
  return (
    <section className="w-full min-w-0 rounded-[10px] border border-slate-800 bg-gradient-to-br from-[#0F172A] to-[#1E3A5F] p-6 shadow-inner">
      <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-sky-300">
        Framework behind this
      </p>
      <div className="mt-4 whitespace-pre-wrap text-[13px] leading-relaxed text-white/80">{body}</div>
    </section>
  );
}
