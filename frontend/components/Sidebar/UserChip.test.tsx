import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import UserChip from "./UserChip";

describe("UserChip", () => {
  it("renders name, email, and initials", () => {
    render(
      <UserChip
        name="Jordan Smith"
        email="jordan@finnwise.test"
        onSignOut={jest.fn()}
      />,
    );

    expect(screen.getByText("Jordan Smith")).toBeInTheDocument();
    expect(screen.getByText("jordan@finnwise.test")).toBeInTheDocument();
    expect(screen.getByText("JS")).toBeInTheDocument();
  });

  it("calls onSignOut from the menu", async () => {
    const user = userEvent.setup();
    const onSignOut = jest.fn().mockResolvedValue(undefined);
    render(
      <UserChip
        name="Sam Lee"
        email="sam@finnwise.test"
        onSignOut={onSignOut}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Sam Lee/i }));
    await user.click(await screen.findByRole("menuitem", { name: /sign out/i }));

    expect(onSignOut).toHaveBeenCalledTimes(1);
  });
});
