import { render, screen } from "@testing-library/react";

import { SebiFooter } from "./SebiFooter";

describe("SebiFooter", () => {
  it("renders persistent SEBI disclaimer copy", () => {
    render(<SebiFooter />);
    expect(
      screen.getByRole("contentinfo", { name: /SEBI regulatory disclaimer/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not constitute registered investment advice/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Investment Advisers\) Regulations 2013/i)).toBeInTheDocument();
  });
});
