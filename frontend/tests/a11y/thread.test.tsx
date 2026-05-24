/** @jest-environment jsdom */

import { render } from "@testing-library/react";
import { axe } from "jest-axe";

import { InstrumentCard } from "@/app/(app)/thread/_components/InstrumentCard";

describe("Thread a11y", () => {
  it("InstrumentCard has no axe violations", async () => {
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
    expect(await axe(container)).toHaveNoViolations();
  });
});
