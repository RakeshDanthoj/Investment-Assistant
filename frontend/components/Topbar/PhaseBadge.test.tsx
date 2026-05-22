/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { PhaseBadge } from "./PhaseBadge";

describe("PhaseBadge", () => {
  it("always renders the Phase 1 tester pill", () => {
    render(<PhaseBadge />);
    expect(screen.getByLabelText("Phase 1 tester build")).toHaveTextContent("Phase 1 tester");
  });
});
