/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ReasoningGapPanel } from "./ReasoningGapPanel";

describe("ReasoningGapPanel", () => {
  it("renders three gap items with Map links", () => {
    render(
      <ReasoningGapPanel
        gaps={{
          insufficient_history: false,
          items: [
            {
              gap_type: "direction_magnitude_mismatch",
              gap_name: "Direction-correct, magnitude-wrong",
              pattern_explanation: "Mechanism correct but market partial.",
              linked_map_module_id: "a1000001-0001-4000-8000-000000000001",
              linked_map_module_name: "Direction vs magnitude",
            },
            {
              gap_type: "narrative_anchoring",
              gap_name: "Anchored on narrative",
              pattern_explanation: "Business right, mechanism wrong.",
              linked_map_module_id: "a1000001-0001-4000-8000-000000000002",
              linked_map_module_name: "Narrative vs mechanism",
            },
            {
              gap_type: "sector_concentration",
              gap_name: "Sector concentration in your predictions",
              pattern_explanation: "Most calls in banking.",
              linked_map_module_id: "a1000001-0001-4000-8000-000000000003",
              linked_map_module_name: "Sector concentration",
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("Reasoning gap analysis")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /The Map:/ })).toHaveLength(3);
    expect(screen.getByRole("link", { name: /Direction vs magnitude/ })).toHaveAttribute(
      "href",
      "/map?module=a1000001-0001-4000-8000-000000000001",
    );
  });

  it("suppresses items when history is insufficient", () => {
    render(
      <ReasoningGapPanel
        gaps={{ insufficient_history: true, items: [] }}
      />,
    );
    expect(screen.getByTestId("reasoning-gap-empty")).toBeInTheDocument();
    expect(screen.queryByTestId("reasoning-gap-direction_magnitude_mismatch")).not.toBeInTheDocument();
  });

  it("calls onRefresh when Refresh is clicked", async () => {
    const user = userEvent.setup();
    const onRefresh = jest.fn();
    render(
      <ReasoningGapPanel
        gaps={{ insufficient_history: true, items: [] }}
        onRefresh={onRefresh}
      />,
    );
    await user.click(screen.getByTestId("reasoning-gap-refresh"));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
