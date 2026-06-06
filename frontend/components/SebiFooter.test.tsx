/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";

import { SebiFooter } from "./SebiFooter";

describe("SebiFooter", () => {
  it("renders persistent SEBI disclaimer copy on desktop", () => {
    render(<SebiFooter />);
    expect(
      screen.getByRole("contentinfo", { name: /SEBI regulatory disclaimer/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not constitute registered investment advice/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Investment Advisers\) Regulations 2013/i)).toBeInTheDocument();
  });

  it("expands the mobile disclaimer summary on tap", () => {
    render(<SebiFooter />);
    fireEvent.click(screen.getByRole("button", { name: /SEBI disclaimer/i }));
    expect(
      screen.getAllByText(/does not constitute registered investment advice/i).length,
    ).toBeGreaterThan(0);
  });
});
