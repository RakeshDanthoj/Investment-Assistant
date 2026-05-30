import { fireEvent, render, screen } from "@testing-library/react";

import ChecklistPanel from "./ChecklistPanel";
import type { EditorialChecklistPayload } from "./PublishGate";

const passValidation = {
  status: "PASS" as const,
  ungrounded: [],
  missing_provenance: [],
  comparative_flags: [],
};

const passChecklist: EditorialChecklistPayload = {
  all_automated_pass: true,
  items: [
    {
      key: "numbers",
      label: "Numbers grounded",
      automated: true,
      status: "PASS",
      message: "Number validator PASS.",
    },
    {
      key: "dissent",
      label: "Dissent present",
      automated: true,
      status: "PASS",
      message: "Dissent length ok.",
    },
    {
      key: "evidence_freshness",
      label: "Evidence fresh",
      automated: true,
      status: "PASS",
      message: "Within 18 months.",
    },
    {
      key: "sebi_compliance",
      label: "SEBI clean",
      automated: true,
      status: "PASS",
      message: "SEBI language scan PASS.",
    },
    {
      key: "plain_english",
      label: "Plain English",
      automated: false,
      status: "PENDING",
      message: "Editor must confirm.",
    },
  ],
};

describe("ChecklistPanel", () => {
  const baseProps = {
    draftId: "00000000-0000-4000-8000-000000000001",
    onReload: jest.fn().mockResolvedValue(undefined),
  };

  it("disables Publish until automated checks pass and plain English is confirmed", async () => {
    const openedAtMs = Date.now();
    const onPublish = jest.fn().mockResolvedValue(undefined);
    const onRegenerate = jest.fn().mockResolvedValue(undefined);

    render(
      <ChecklistPanel
        {...baseProps}
        openedAtMs={openedAtMs}
        onPublish={onPublish}
        onRegenerate={onRegenerate}
        numberValidation={passValidation}
        editorialChecklist={passChecklist}
      />,
    );

    const publishBtn = screen.getByTestId("publish-draft-btn");
    expect(publishBtn).toBeDisabled();

    expect(screen.getAllByText("PASS")).toHaveLength(4);
    expect(screen.getByTestId("checklist-status-plain_english")).toHaveTextContent("PENDING");

    fireEvent.click(screen.getByRole("checkbox"));

    expect(publishBtn).not.toBeDisabled();
    fireEvent.click(publishBtn);

    expect(onPublish).toHaveBeenCalledTimes(1);
    expect(typeof onPublish.mock.calls[0][0]).toBe("number");
  });

  it("keeps Publish disabled when automated checklist fails", () => {
    render(
      <ChecklistPanel
        {...baseProps}
        openedAtMs={Date.now()}
        onPublish={jest.fn()}
        onRegenerate={jest.fn()}
        numberValidation={passValidation}
        editorialChecklist={{
          all_automated_pass: false,
          items: passChecklist.items.map((item) =>
            item.key === "sebi_compliance"
              ? { ...item, status: "FAIL", message: "Found buy language." }
              : item,
          ),
        }}
      />,
    );

    fireEvent.click(screen.getByRole("checkbox"));

    expect(screen.getByTestId("publish-draft-btn")).toBeDisabled();
    expect(screen.getByTestId("publish-gate-fail")).toBeInTheDocument();
    expect(screen.getByTestId("checklist-status-sebi_compliance")).toHaveTextContent("FAIL");
  });

  it("keeps Publish disabled when number validator fails", () => {
    render(
      <ChecklistPanel
        {...baseProps}
        openedAtMs={Date.now()}
        onPublish={jest.fn()}
        onRegenerate={jest.fn()}
        numberValidation={{
          status: "FAIL",
          ungrounded: [{ number: "42", sentence: "Value is 42.", index: 0 }],
          missing_provenance: [],
          comparative_flags: [],
        }}
        editorialChecklist={passChecklist}
      />,
    );

    fireEvent.click(screen.getByRole("checkbox"));

    expect(screen.getByTestId("publish-draft-btn")).toBeDisabled();
    expect(screen.getByTestId("publish-gate-fail")).toBeInTheDocument();
  });
});
