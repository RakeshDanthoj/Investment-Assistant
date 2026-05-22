/** @jest-environment jsdom */

import { render, screen, waitFor } from "@testing-library/react";

import { SignalQueueTable } from "./SignalQueueClient";

jest.mock("../../../lib/api", () => ({
  getApiBaseUrl: () => "http://localhost:8000",
}));

describe("SignalQueueTable", () => {
  it("renders a pending row with review link href", () => {
    render(
      <SignalQueueTable
        loading={false}
        rows={[
          {
            id: "queue-row-1",
            card_id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_id: "signal-1",
            status: "pending",
            gate: "medium",
            reason: "one_to_two_direct_sources:2",
            payload: {},
            created_at: "2026-05-22T10:30:00.000Z",
          },
        ]}
      />,
    );

    expect(screen.getByText(/one to two direct sources · 2/i)).toBeInTheDocument();
    expect(screen.getByText("medium")).toBeInTheDocument();

    const reviewLink = screen.getByRole("link", { name: "Open review" });
    expect(reviewLink).toHaveAttribute(
      "href",
      "/admin/review/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    );
  });

  it("shows empty state when there are no pending rows", () => {
    render(<SignalQueueTable loading={false} rows={[]} />);
    expect(screen.getByText(/no medium-confidence signal hits are pending review/i)).toBeInTheDocument();
  });
});

describe("SignalQueueClient", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("fetches pending rows from the admin signal-queue API", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => [
        {
          id: "q1",
          card_id: "card-abc",
          signal_id: "sig-1",
          status: "pending",
          gate: "medium",
          reason: "partial_match_only_sources:1",
          payload: {},
          created_at: "2026-05-22T08:00:00.000Z",
        },
      ],
    });

    const SignalQueueClient = (await import("./SignalQueueClient")).default;
    render(<SignalQueueClient />);

    await waitFor(() => {
      expect(screen.getByRole("link", { name: "Open review" })).toHaveAttribute(
        "href",
        "/admin/review/card-abc",
      );
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/admin/signal-queue?status=pending",
      { cache: "no-store" },
    );
  });
});
