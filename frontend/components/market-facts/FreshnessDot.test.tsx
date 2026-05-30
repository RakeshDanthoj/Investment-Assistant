import { render, screen } from "@testing-library/react";

import { FreshnessDot } from "./FreshnessDot";

describe("FreshnessDot", () => {
  it("maps fresh status to accessible label", () => {
    render(<FreshnessDot status="fresh" />);
    expect(screen.getByLabelText("Data freshness: Fresh")).toBeInTheDocument();
  });

  it("maps stale status to accessible label", () => {
    render(<FreshnessDot status="stale" />);
    expect(screen.getByLabelText("Data freshness: Stale")).toBeInTheDocument();
  });

  it("maps unavailable status to accessible label", () => {
    render(<FreshnessDot status="unavailable" />);
    expect(screen.getByLabelText("Data freshness: Unavailable")).toBeInTheDocument();
  });
});
