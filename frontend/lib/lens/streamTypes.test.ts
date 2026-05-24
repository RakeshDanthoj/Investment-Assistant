import {
  applyStreamStep,
  initialPipelineStepStatuses,
  progressPercentFromSteps,
} from "./streamTypes";

describe("applyStreamStep", () => {
  it("transitions pending to active to done across milestones", () => {
    let statuses = initialPipelineStepStatuses();

    statuses = applyStreamStep(statuses, {
      event: "step",
      index: 0,
      name: "Factor DB queried",
      status: "active",
    });
    expect(statuses[0]).toBe("active");

    statuses = applyStreamStep(statuses, {
      event: "step",
      index: 0,
      name: "Factor DB queried",
      status: "done",
    });
    expect(statuses[0]).toBe("done");

    statuses = applyStreamStep(statuses, {
      event: "step",
      index: 1,
      name: "Macro signals retrieved",
      status: "active",
    });
    expect(statuses[1]).toBe("active");
    expect(statuses[0]).toBe("done");
  });
});

describe("progressPercentFromSteps", () => {
  it("increases as steps complete", () => {
    const empty = progressPercentFromSteps(initialPipelineStepStatuses());
    const halfDone = progressPercentFromSteps([
      "done",
      "done",
      "done",
      "active",
      "pending",
      "pending",
    ]);
    const allDone = progressPercentFromSteps([
      "done",
      "done",
      "done",
      "done",
      "done",
      "done",
    ]);

    expect(halfDone).toBeGreaterThan(empty);
    expect(allDone).toBe(100);
  });
});
