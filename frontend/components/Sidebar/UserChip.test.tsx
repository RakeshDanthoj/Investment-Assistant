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

  it("links to account settings from the menu", async () => {
    const user = userEvent.setup();
    render(
      <UserChip
        name="Sam Lee"
        email="sam@finnwise.test"
        onSignOut={jest.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Sam Lee/i }));

    const accountLink = await screen.findByRole("menuitem", { name: /account/i });
    expect(accountLink).toHaveAttribute("href", "/account");
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
