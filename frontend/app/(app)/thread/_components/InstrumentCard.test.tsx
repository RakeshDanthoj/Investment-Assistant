/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { InstrumentCard } from "./InstrumentCard";

const forbidden = /\b(buy|sell|hold)\b|₹\s*\d+/i;

describe("InstrumentCard", () => {
  it("does not surface advisory verbs or rupee price targets in rendered copy", () => {
    const { container } = render(
      <InstrumentCard
        row={{
          instrument_id: "INDIGO",
          signal_label: "headwind signal",
          reasoning: "Aviation faces higher input costs while demand stays elastic.",
          entry_conditions: ["ATF quotes remain elevated vs trailing quarter"],
          exit_conditions: ["Policy intervention caps pass-through"],
        }}
      />,
    );
    const text = container.textContent ?? "";
    expect(text.toLowerCase()).not.toMatch(forbidden);
    expect(screen.getByText("Why we labelled it this way")).toBeInTheDocument();
  });
});
