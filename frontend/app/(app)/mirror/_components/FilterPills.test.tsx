/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";

import { FilterPills } from "./FilterPills";

describe("FilterPills", () => {
  it("calls onStatusChange when a filter pill is selected", () => {
    const onStatusChange = jest.fn();
    render(<FilterPills status={null} onStatusChange={onStatusChange} />);

    fireEvent.click(screen.getByRole("radio", { name: "Resolved" }));
    expect(onStatusChange).toHaveBeenCalledWith("resolved");

    fireEvent.click(screen.getByRole("radio", { name: "All" }));
    expect(onStatusChange).toHaveBeenCalledWith(null);
  });
});
