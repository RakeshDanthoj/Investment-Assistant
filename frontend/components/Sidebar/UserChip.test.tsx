import { fireEvent, render, screen, waitFor } from "@testing-library/react";

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
    const onSignOut = jest.fn().mockResolvedValue(undefined);
    render(
      <UserChip
        name="Sam Lee"
        email="sam@finnwise.test"
        onSignOut={onSignOut}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Sam Lee/i }));
    fireEvent.click(await screen.findByRole("menuitem", { name: /sign out/i }));

    await waitFor(() => expect(onSignOut).toHaveBeenCalledTimes(1));
  });
});
