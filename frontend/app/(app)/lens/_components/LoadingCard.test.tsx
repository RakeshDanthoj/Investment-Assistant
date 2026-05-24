/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { LENS_DISCLAIMER, LENS_PIPELINE_STEPS } from "@/lib/lens/pipelineSteps";

import { PipelineStep } from "./PipelineStep";

describe("Lens loading PRD copy", () => {
  it("lists six pipeline steps and the disclaimer verbatim", () => {
    expect(LENS_PIPELINE_STEPS).toHaveLength(6);
    expect(LENS_PIPELINE_STEPS[0]).toBe("Factor DB queried");
    expect(LENS_PIPELINE_STEPS[5]).toBe("Validating numbers against Evidence");
    expect(LENS_DISCLAIMER).toBe(
      "Every number is validated against the Evidence layer before display.",
    );
  });
});

describe("PipelineStep", () => {
  it("transitions pending to active to done", () => {
    const { rerender } = render(
      <ul>
        <PipelineStep index={0} label="Factor DB queried" status="pending" />
      </ul>,
    );
    expect(screen.getByText("1")).toBeInTheDocument();

    rerender(
      <ul>
        <PipelineStep index={0} label="Factor DB queried" status="active" />
      </ul>,
    );
    expect(screen.getByText("Factor DB queried")).toHaveClass("text-[#1A4FCC]");

    rerender(
      <ul>
        <PipelineStep index={0} label="Factor DB queried" status="done" />
      </ul>,
    );
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });
});
