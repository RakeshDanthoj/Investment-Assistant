import { render, screen } from "@testing-library/react";

import { HoldingCallout } from "./HoldingCallout";

describe("HoldingCallout", () => {
  it("renders nothing when intersection is empty", () => {
    const { container } = render(<HoldingCallout intersections={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows per-holding callout when intersection is non-empty", () => {
    render(
      <HoldingCallout
        intersections={[
          {
            instrument_id: "HDFCBANK",
            holdingDisplayName: "HDFC Bank Ltd",
            signal_label: "Headwind signal",
          },
        ]}
      />,
    );
    expect(screen.getByText(/What this means for your HDFC Bank Ltd/i)).toBeInTheDocument();
    expect(screen.getByText(/HDFCBANK/i)).toBeInTheDocument();
  });
});
