import { render, screen } from "@testing-library/react";

import PublishGate, {
  automatedChecklistFailures,
  isEditorialChecklistReady,
  isNumberValidationPass,
} from "./PublishGate";

const passValidation = {
  status: "PASS" as const,
  ungrounded: [],
  missing_provenance: [],
  comparative_flags: [],
};

const passChecklist = {
  all_automated_pass: true,
  items: [
    {
      key: "numbers",
      label: "Numbers grounded",
      automated: true,
      status: "PASS" as const,
    },
    {
      key: "plain_english",
      label: "Plain English",
      automated: false,
      status: "PENDING" as const,
    },
  ],
};

describe("PublishGate", () => {
  it("shows loading state", () => {
    render(<PublishGate validation={null} loading />);
    expect(screen.getByTestId("publish-gate-loading")).toBeInTheDocument();
  });

  it("shows error when validator unavailable", () => {
    render(<PublishGate validation={null} error="network error" />);
    expect(screen.getByTestId("publish-gate-error")).toHaveTextContent("network error");
  });

  it("shows PASS when number validation and checklist pass", () => {
    render(<PublishGate validation={passValidation} checklist={passChecklist} />);
    expect(screen.getByTestId("publish-gate-pass")).toBeInTheDocument();
    expect(isNumberValidationPass(passValidation)).toBe(true);
    expect(isEditorialChecklistReady(passChecklist)).toBe(true);
  });

  it("renders checklist failures and ungrounded diff on FAIL", () => {
    render(
      <PublishGate
        validation={{
          status: "FAIL",
          ungrounded: [
            {
              number: "99.9%",
              sentence: "Analysts cite 99.9% certainty [JUDGED].",
              index: 0,
            },
          ],
          missing_provenance: [],
          comparative_flags: ["doubled"],
        }}
        checklist={{
          all_automated_pass: false,
          items: [
            {
              key: "sebi_compliance",
              label: "No buy language",
              automated: true,
              status: "FAIL",
              message: "Found buy recommendation language",
            },
          ],
        }}
      />,
    );
    expect(screen.getByTestId("publish-gate-fail")).toBeInTheDocument();
    expect(screen.getByText("99.9%")).toBeInTheDocument();
    expect(screen.getByTestId("publish-gate-checklist-failures")).toHaveTextContent("No buy language");
    expect(automatedChecklistFailures(passChecklist)).toHaveLength(0);
    expect(screen.getByTestId("publish-gate-soft-warnings")).toHaveTextContent("doubled");
  });
});
