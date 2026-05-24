/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";

import { QueryInput } from "@/app/(app)/lens/_components/QueryInput";

describe("Lens a11y", () => {
  it("QueryInput has no axe violations", async () => {
    const { container } = render(
      <QueryInput
        queryText=""
        sector={null}
        horizon={null}
        onQueryChange={() => undefined}
        onSectorChange={() => undefined}
        onHorizonChange={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    expect(screen.getByPlaceholderText(/Describe an event/i)).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });
});
