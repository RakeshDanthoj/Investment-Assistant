"use client";

type CurrentOriginalToggleProps = {
  view: "current" | "original";
  onChange: (view: "current" | "original") => void;
};

export function CurrentOriginalToggle({ view, onChange }: CurrentOriginalToggleProps) {
  return (
    <div
      role="group"
      aria-label="View mode"
      className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-sm"
    >
      <button
        type="button"
        onClick={() => {
          onChange("current");
        }}
        className={`rounded-md px-3 py-1.5 font-mono text-[11px] font-medium transition-colors ${
          view === "current"
            ? "bg-finnwise-blue text-white"
            : "text-slate-600 hover:bg-slate-50"
        }`}
      >
        Current
      </button>
      <button
        type="button"
        onClick={() => {
          onChange("original");
        }}
        className={`rounded-md px-3 py-1.5 font-mono text-[11px] font-medium transition-colors ${
          view === "original"
            ? "bg-finnwise-blue text-white"
            : "text-slate-600 hover:bg-slate-50"
        }`}
      >
        Original
      </button>
    </div>
  );
}
