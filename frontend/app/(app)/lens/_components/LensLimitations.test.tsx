import { render, screen } from "@testing-library/react";

import {
  LENS_LIMITATIONS_BODY,
  LENS_LIMITATIONS_TITLE,
  LensLimitations,
} from "./LensLimitations";

describe("LensLimitations", () => {
  it("renders mandatory block with exact PRD copy", () => {
    render(<LensLimitations />);
    expect(screen.getByTestId("lens-limitations")).toBeInTheDocument();
    expect(screen.getByText(LENS_LIMITATIONS_TITLE)).toBeInTheDocument();
    expect(screen.getByText(LENS_LIMITATIONS_BODY)).toBeInTheDocument();
  });
});
