import { fireEvent, render, screen } from "@testing-library/react";

import ChecklistPanel from "./ChecklistPanel";

describe("ChecklistPanel", () => {
  it("disables Publish until all five checklist items are checked", async () => {
    const openedAtMs = Date.now();
    const onPublish = jest.fn().mockResolvedValue(undefined);
    const onRegenerate = jest.fn().mockResolvedValue(undefined);

    render(
      <ChecklistPanel
        openedAtMs={openedAtMs}
        onPublish={onPublish}
        onRegenerate={onRegenerate}
      />,
    );

    const publishBtn = screen.getByTestId("publish-draft-btn");
    expect(publishBtn).toBeDisabled();

    const boxes = screen.getAllByRole("checkbox");
    expect(boxes).toHaveLength(5);

    for (const box of boxes) {
      fireEvent.click(box);
    }

    expect(publishBtn).not.toBeDisabled();
    fireEvent.click(publishBtn);

    expect(onPublish).toHaveBeenCalledTimes(1);
    expect(typeof onPublish.mock.calls[0][0]).toBe("number");
  });
});
