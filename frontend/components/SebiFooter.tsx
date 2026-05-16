const SEBI_DISCLAIMER =
  "FinnWise generates AI-powered analysis for educational and research purposes only. " +
  "It does not constitute registered investment advice under SEBI (Investment Advisers) Regulations 2013.";

export function SebiFooter() {
  return (
    <footer
      role="contentinfo"
      aria-label="SEBI regulatory disclaimer"
      className="shrink-0 border-t border-[#FECACA] bg-[#FEF2F2] px-4 py-3"
    >
      <p className="font-mono text-[10px] leading-relaxed text-finnwise-red">
        {SEBI_DISCLAIMER}
      </p>
    </footer>
  );
}
