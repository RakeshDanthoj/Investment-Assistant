/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { BiasFlags } from "./BiasFlags";

import type { CardDetailResponse } from "@/lib/cards/threadTypes";

const baseAudit: CardDetailResponse["bias_audit"] = {
  flags: [],
  monitored: [],
};

describe("BiasFlags", () => {
  it("renders flagged biases with amber treatment", () => {
    render(
      <BiasFlags
        audit={{
          ...baseAudit,
          flags: [
            {
              id: "recency",
              label: "Recency bias",
              status: "flagged",
              detail: "70% of sources are from the last 30 days.",
            },
          ],
        }}
      />,
    );
    const flagged = screen.getByTestId("bias-flag-recency");
    expect(flagged).toHaveClass("border-amber-200");
    expect(flagged).toHaveClass("bg-[#FFFBEB]");
  });

  it("renders monitored biases with grey treatment", () => {
    render(
      <BiasFlags
        audit={{
          ...baseAudit,
          monitored: [
            {
              id: "anchoring",
              label: "Anchoring bias",
              status: "monitored",
              detail: "Dissent uses a separate LLM prompt.",
            },
          ],
        }}
      />,
    );
    const monitored = screen.getByTestId("bias-monitored-anchoring");
    expect(monitored).toHaveClass("border-slate-200");
    expect(monitored).toHaveClass("bg-slate-50");
  });
});
