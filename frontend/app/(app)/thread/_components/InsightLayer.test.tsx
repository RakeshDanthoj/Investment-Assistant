/** @jest-environment jsdom */

import type { ComponentType } from "react";
import { render, screen } from "@testing-library/react";

import { InsightLayer } from "./InsightLayer";

jest.mock("next/dynamic", () => (loader: () => Promise<{ default: ComponentType<{ cardId: string }> }>) => {
  const { PredictionLogger } = jest.requireMock<{ PredictionLogger: ComponentType<{ cardId: string }> }>(
    "./PredictionLogger",
  );
  void loader();
  return PredictionLogger;
});

jest.mock("./PredictionLogger", () => ({
  PredictionLogger: ({ cardId }: { cardId: string }) => (
    <div data-testid="prediction-logger">{cardId}</div>
  ),
}));

const baseProps = {
  cardId: "card-abc",
  insight_layer: "Insight body",
  instruments: [],
  dissenting_view: "Dissent",
  framework_behind_this: "Framework",
};

describe("InsightLayer prediction logger gating", () => {
  it("renders PredictionLogger before Context is revealed", () => {
    render(<InsightLayer {...baseProps} showPredictionLogger />);
    expect(screen.getByTestId("prediction-logger")).toBeInTheDocument();
  });

  it("hides PredictionLogger after Context is revealed", () => {
    render(<InsightLayer {...baseProps} showPredictionLogger={false} />);
    expect(screen.queryByTestId("prediction-logger")).not.toBeInTheDocument();
  });
});
