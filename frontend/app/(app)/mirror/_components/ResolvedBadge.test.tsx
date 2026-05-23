/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";

import { ResolvedBadge } from "./ResolvedBadge";

describe("ResolvedBadge", () => {
  it("renders nothing when count is zero", () => {
    const { container } = render(<ResolvedBadge count={0} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders pulsing dot and label for a single card", () => {
    const onClick = jest.fn();
    render(<ResolvedBadge count={1} onClick={onClick} />);

    expect(screen.getByTestId("mirror-resolved-badge")).toBeInTheDocument();
    expect(screen.getByTestId("mirror-resolved-badge-pulse")).toHaveClass("thread-signal-pulse");
    expect(screen.getByLabelText("1 card resolved — ready to grade")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("mirror-resolved-badge"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("uses plural copy for multiple cards", () => {
    render(<ResolvedBadge count={3} />);
    expect(screen.getByLabelText("3 cards resolved — ready to grade")).toBeInTheDocument();
  });
});
