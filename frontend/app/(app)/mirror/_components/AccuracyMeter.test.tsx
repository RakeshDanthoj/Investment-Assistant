/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { AccuracyMeterGroup } from "./AccuracyMeter";

describe("AccuracyMeter", () => {
  it("renders three independent labelled bars", () => {
    render(
      <AccuracyMeterGroup mechanism="correct" business="partial" market="incorrect" />,
    );

    expect(screen.getByTestId("accuracy-meter-mechanism")).toBeInTheDocument();
    expect(screen.getByTestId("accuracy-meter-business")).toBeInTheDocument();
    expect(screen.getByTestId("accuracy-meter-market")).toBeInTheDocument();

    expect(screen.getByText("✓ Correct")).toBeInTheDocument();
    expect(screen.getByText("~ Partial")).toBeInTheDocument();
    expect(screen.getByText("✗ Incorrect")).toBeInTheDocument();
  });
});
