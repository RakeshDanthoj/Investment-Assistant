import { Alert, AlertDescription } from "@/components/ui/alert";

const SEBI_DISCLAIMER =
  "FinnWise generates AI-powered analysis for educational and research purposes only. " +
  "It does not constitute registered investment advice under SEBI (Investment Advisers) Regulations 2013.";

export function SebiFooter() {
  return (
    <footer role="contentinfo" aria-label="SEBI regulatory disclaimer">
      <Alert className="shrink-0 rounded-none border-x-0 border-b-0 border-[#FECACA] bg-[#FEF2F2] px-4 py-3">
        <AlertDescription className="font-mono text-[10px] leading-relaxed text-finnwise-red">
          {SEBI_DISCLAIMER}
        </AlertDescription>
      </Alert>
    </footer>
  );
}
