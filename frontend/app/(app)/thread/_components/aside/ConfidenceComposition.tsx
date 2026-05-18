"use client";

type ConfidenceCompositionProps = {
  measured: number;
  modelled: number;
  judged: number;
};

export function ConfidenceComposition({ measured, modelled, judged }: ConfidenceCompositionProps) {
  const mPct = Math.round(measured * 100);
  const moPct = Math.round(modelled * 100);
  const jPct = Math.max(0, 100 - mPct - moPct);

  return (
    <section className="rounded-[10px] border border-slate-200 bg-white p-4">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
        Confidence composition
      </p>
      <div className="mt-3 flex h-3 overflow-hidden rounded-full border border-slate-200">
        <span className="bg-finnwise-blue" style={{ width: `${mPct}%` }} title="Measured" />
        <span className="bg-finnwise-green" style={{ width: `${moPct}%` }} title="Modelled" />
        <span className="bg-finnwise-amber" style={{ width: `${jPct}%` }} title="Judged" />
      </div>
      <ul className="mt-3 space-y-1 font-mono text-[10px] text-slate-600">
        <li>
          <span className="inline-block h-2 w-2 rounded-full bg-finnwise-blue align-middle" /> Measured{" "}
          {mPct}%
        </li>
        <li>
          <span className="inline-block h-2 w-2 rounded-full bg-finnwise-green align-middle" /> Modelled{" "}
          {moPct}%
        </li>
        <li>
          <span className="inline-block h-2 w-2 rounded-full bg-finnwise-amber align-middle" /> Judged{" "}
          {jPct}%
        </li>
      </ul>
    </section>
  );
}
