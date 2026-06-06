"use client";

import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

const SEBI_DISCLAIMER =
  "FinnWise generates AI-powered analysis for educational and research purposes only. " +
  "It does not constitute registered investment advice under SEBI (Investment Advisers) Regulations 2013.";

export function SebiFooter() {
  const [expanded, setExpanded] = useState(false);

  return (
    <footer role="contentinfo" aria-label="SEBI regulatory disclaimer">
      <div className="min-[860px]:hidden">
        <Collapsible open={expanded} onOpenChange={setExpanded}>
          <CollapsibleTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              className="h-auto w-full rounded-none border-x-0 border-t border-[#FECACA] bg-[#FEF2F2] px-4 py-2 text-left hover:bg-[#FEF2F2]"
              aria-expanded={expanded}
            >
              <span className="font-mono text-[10px] leading-snug text-finnwise-red">
                SEBI disclaimer · educational use only
              </span>
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <Alert className="rounded-none border-x-0 border-b-0 border-t-0 border-[#FECACA] bg-[#FEF2F2] px-4 py-3">
              <AlertDescription className="font-mono text-[10px] leading-relaxed text-finnwise-red">
                {SEBI_DISCLAIMER}
              </AlertDescription>
            </Alert>
          </CollapsibleContent>
        </Collapsible>
      </div>

      <Alert className="hidden shrink-0 rounded-none border-x-0 border-b-0 border-[#FECACA] bg-[#FEF2F2] px-4 py-3 min-[860px]:block">
        <AlertDescription className="font-mono text-[10px] leading-relaxed text-finnwise-red">
          {SEBI_DISCLAIMER}
        </AlertDescription>
      </Alert>
    </footer>
  );
}
