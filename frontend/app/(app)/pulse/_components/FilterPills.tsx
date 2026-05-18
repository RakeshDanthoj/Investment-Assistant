"use client";

type FilterPillsProps = {
  options: readonly { id: string; label: string }[];
  selected: string[];
  onChange: (next: string[]) => void;
};

export function FilterPills({ options, selected, onChange }: FilterPillsProps) {
  const selectedSet = new Set(selected);

  function toggle(id: string) {
    if (id === "__all__") {
      onChange([]);
      return;
    }
    const next = new Set(selectedSet);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(Array.from(next));
  }

  const allActive = selected.length === 0;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <button
        type="button"
        onClick={() => toggle("__all__")}
        className={`rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide transition-all duration-150 ease-in-out ${
          allActive
            ? "bg-finnwise-blue text-white"
            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
        }`}
      >
        All
      </button>
      {options.map((opt) => {
        const isOn = selectedSet.has(opt.id);
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => toggle(opt.id)}
            className={`rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide transition-all duration-150 ease-in-out ${
              isOn
                ? "bg-finnwise-blue text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
