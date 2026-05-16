/** Three dots for Questions 1–3 — never a percentage bar (PRD §5). */
type ProgressDotsProps = {
  /** 1-indexed conversational step (1–4). Step 4 = all complete, none active. */
  flowStep: 1 | 2 | 3 | 4;
};

export function ProgressDots({ flowStep }: ProgressDotsProps) {
  const positions = [1, 2, 3] as const;

  return (
    <div className="flex items-center gap-1.5" aria-label="Onboarding progress">
      {positions.map((dot) => {
        const isPast = flowStep > dot;
        const isActive = flowStep === dot && flowStep < 4;

        let className = "h-2 w-2 rounded-full bg-slate-200 transition-transform";
        if (isActive) {
          className =
            "h-2 w-2 scale-[1.2] rounded-full bg-[#1A4FCC] shadow-sm transition-transform";
        } else if (isPast || flowStep === 4) {
          className = "h-2 w-2 rounded-full bg-slate-400 transition-transform";
        }

        return (
          <div key={dot} className={className} aria-current={isActive ? "step" : undefined} />
        );
      })}
    </div>
  );
}
