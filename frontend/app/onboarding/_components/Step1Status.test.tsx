import { fireEvent, render, screen } from "@testing-library/react";

import { Step1Status } from "./Step1Status";

describe("Step1Status", () => {
  it("calls onSelect and shows selected styling", () => {
    const onSelect = jest.fn();
    const { rerender } = render(<Step1Status selected={null} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole("button", { name: /Starting fresh/i }));
    expect(onSelect).toHaveBeenCalledWith("starting_fresh");

    rerender(<Step1Status selected="starting_fresh" onSelect={onSelect} />);
    expect(screen.getByRole("button", { name: /Starting fresh/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
