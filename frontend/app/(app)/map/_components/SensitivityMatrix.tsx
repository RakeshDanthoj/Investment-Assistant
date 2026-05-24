import type { MapFactor, MapInstrument, MapSensitivityCell } from "@/lib/map/types";

const FRESHNESS_DOT: Record<string, string> = {
  green: "bg-emerald-500",
  amber: "bg-amber-400",
  red: "bg-rose-500",
};

type SensitivityMatrixProps = {
  factors: MapFactor[];
  instruments: MapInstrument[];
  sensitivities: Record<string, Record<string, MapSensitivityCell>>;
  totalInstrumentCount: number;
};

export function SensitivityMatrix({
  factors,
  instruments,
  sensitivities,
  totalInstrumentCount,
}: SensitivityMatrixProps) {
  const sortedFactors = [...factors].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <section data-testid="sensitivity-matrix">
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="font-display text-lg font-semibold text-slate-900">Factor sensitivities</h2>
        <p className="font-mono text-[10px] uppercase tracking-wide text-slate-500">
          Showing {instruments.length} of {totalInstrumentCount} NSE names
        </p>
      </div>
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="min-w-full border-collapse text-left text-[12px]">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="sticky left-0 z-10 bg-slate-50 px-3 py-2 font-semibold text-slate-700">
                Ticker
              </th>
              {sortedFactors.map((f) => (
                <th key={f.slug} className="px-2 py-2 font-medium text-slate-600" title={f.description}>
                  <span className="block max-w-[72px] truncate">{f.display_name}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {instruments.map((inst) => (
              <tr key={inst.id} className="border-b border-slate-100 last:border-0">
                <td className="sticky left-0 z-10 bg-white px-3 py-2 font-mono font-semibold text-slate-800">
                  {inst.ticker}
                </td>
                {sortedFactors.map((f) => {
                  const cell = sensitivities[inst.ticker]?.[f.slug];
                  if (!cell) {
                    return (
                      <td key={f.slug} className="px-2 py-2 text-center text-slate-300">
                        —
                      </td>
                    );
                  }
                  return (
                    <td key={f.slug} className="px-2 py-2 text-center">
                      <span
                        className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-800"
                        title={`${cell.mmj_tag} · ${cell.source_url}`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${FRESHNESS_DOT[cell.freshness] ?? FRESHNESS_DOT.green}`}
                          aria-hidden
                        />
                        {cell.sensitivity > 0 ? `+${cell.sensitivity}` : cell.sensitivity}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[11px] text-slate-500">
        Each cell is MMJ-tagged with a source URL (Phase 1 invariant). Dot colour = evidence freshness.
      </p>
    </section>
  );
}
