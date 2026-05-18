/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { DissentingView } from "./DissentingView";

describe("DissentingView", () => {
  it("renders on every card when dissent text is provided", () => {
    render(
      <DissentingView text="Closure may be short-lived — markets may already reflect disruption risk." />,
    );
    expect(screen.getByTestId("dissenting-view")).toBeInTheDocument();
    expect(screen.getByText(/dissenting view/i)).toBeInTheDocument();
  });
});
