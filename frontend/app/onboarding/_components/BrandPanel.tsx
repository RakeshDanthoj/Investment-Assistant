/** PRD §5 Screen 1 — fixed 420px brand column; hidden below lg. */
export function BrandPanel() {
  return (
    <aside className="relative hidden min-h-screen w-[420px] flex-none flex-col justify-between overflow-hidden bg-slate-900 p-10 text-white lg:flex">
      <div>
        <p className="font-display text-[28px] font-normal tracking-tight">
          finn<span className="text-finnwise-blue">wise</span>
        </p>
        <p className="font-display mt-8 text-[22px] italic leading-relaxed text-slate-200">
          &ldquo;The first thing you see should feel like a question, not a form.&rdquo;
        </p>
        <ul className="mt-10 space-y-4 text-sm text-slate-300">
          <li className="flex gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-finnwise-blue" />
            Event-led intelligence for Indian markets
          </li>
          <li className="flex gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-finnwise-blue" />
            Transparency before conclusion — confidence is visible
          </li>
          <li className="flex gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-finnwise-blue" />
            Educational framing; not personalised investment advice
          </li>
        </ul>
      </div>
      <p className="font-mono text-[10px] leading-relaxed text-slate-500">
        © FinnWise. All rights reserved.
      </p>
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 top-24 h-80 w-80 rounded-full bg-finnwise-blue/10 blur-3xl"
      />
    </aside>
  );
}
