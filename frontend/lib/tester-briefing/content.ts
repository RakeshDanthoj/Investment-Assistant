/** Committed tester briefing copy — mirrors `notes/tester-briefing.md` (local draft). */

export type BriefingSection = {
  title: string;
  paragraphs: string[];
  bullets?: string[];
};

export const TESTER_BRIEFING_SECTIONS: readonly BriefingSection[] = [
  {
    title: "What FinnWise Phase 1 is",
    paragraphs: [
      "FinnWise Phase 1 is a research preview for invited testers. You will explore educational event intelligence — not personalised investment advice.",
      "The Pulse, Thread, and onboarding surfaces are live. Mirror and Lens are Phase 2 placeholders.",
    ],
  },
  {
    title: "SEBI framing — educational analysis only",
    paragraphs: [
      "FinnWise generates AI-powered analysis for educational and research purposes only. It does not constitute registered investment advice under SEBI (Investment Advisers) Regulations 2013.",
      "Every screen shows a persistent SEBI disclaimer. Do not treat card content as a buy, sell, or hold recommendation.",
    ],
    bullets: [
      "No rupee price targets or return promises",
      "No personalised portfolio advice",
      "No real-money execution through FinnWise",
    ],
  },
  {
    title: "Do not make real-money decisions based on this app",
    paragraphs: [
      "You must not make real investment, trading, or allocation decisions based solely on FinnWise output during this test.",
      "Use the product to learn how macro events connect to instruments — compare against your own research and licensed advisers.",
    ],
  },
  {
    title: "What we need from you",
    paragraphs: [
      "Honest feedback on clarity, bias flags, dissenting views, and whether the analysis feels misleading.",
      "Report bugs, confusing copy, or anything that feels like regulated advice.",
    ],
    bullets: [
      "Feedback channel: reply to your invite email or the Product Owner contact in your invite",
      "Expect 3+ short sessions during Month 3",
      "Optional: note one “I had not considered that” moment from the dissenting view",
    ],
  },
  {
    title: "Acceptance",
    paragraphs: [
      "By checking the box below and clicking Accept, you confirm you have read this briefing, understand the educational-only scope, and will not rely on FinnWise for real-money investment decisions.",
      "Your acceptance is recorded with a timestamp and IP address for compliance records.",
    ],
  },
] as const;
