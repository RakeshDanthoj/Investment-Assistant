/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { QueryInput } from "./QueryInput";

describe("QueryInput", () => {
  it("disables Generate until input exceeds 10 characters", () => {
    const onSubmit = jest.fn();
    const { rerender } = render(
      <QueryInput
        queryText=""
        sector={null}
        horizon={null}
        onQueryChange={jest.fn()}
        onSectorChange={jest.fn()}
        onHorizonChange={jest.fn()}
        onSubmit={onSubmit}
      />,
    );

    const button = screen.getByRole("button", { name: /generate card/i });
    expect(button).toBeDisabled();

    const props = {
      queryText: "12345678901",
      sector: null as string | null,
      horizon: null as import("@/lib/onboarding/state").Horizon | null,
      onQueryChange: jest.fn(),
      onSectorChange: jest.fn(),
      onHorizonChange: jest.fn(),
      onSubmit,
    };
    rerender(<QueryInput {...props} />);
    expect(screen.getByRole("button", { name: /generate card/i })).not.toBeDisabled();
  });

  it("shows the PRD time-estimate note", () => {
    render(
      <QueryInput
        queryText=""
        sector={null}
        horizon={null}
        onQueryChange={jest.fn()}
        onSectorChange={jest.fn()}
        onHorizonChange={jest.fn()}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.getByText("Cards take 30–90 seconds to generate.")).toBeInTheDocument();
  });
});
