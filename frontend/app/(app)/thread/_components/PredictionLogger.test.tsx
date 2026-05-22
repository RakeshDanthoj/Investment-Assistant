/** @jest-environment jsdom */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
  PREDICTION_CONFIRMATION,
  PREDICTION_DISCLAIMER,
  PREDICTION_OPTIONS,
  PredictionLogger,
} from "./PredictionLogger";

jest.mock("../../../../lib/api", () => ({
  getApiBaseUrl: () => "http://localhost:8000",
}));

const mockGetSession = jest.fn();

jest.mock("../../../../lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}));

describe("PredictionLogger", () => {
  beforeEach(() => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "tok" } },
    });
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [] }),
    });
  });

  it("renders exact PRD disclaimer copy", () => {
    render(<PredictionLogger cardId="card-1" />);
    expect(screen.getByText(PREDICTION_DISCLAIMER)).toBeInTheDocument();
  });

  it("replaces logger with confirmation after successful submit", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ items: [] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ ok: true }),
      });

    render(<PredictionLogger cardId="card-1" />);

    fireEvent.click(screen.getByRole("option", { name: PREDICTION_OPTIONS[0] }));
    fireEvent.click(screen.getByRole("button", { name: /Log my prediction/i }));

    await waitFor(() => {
      expect(screen.getByText(PREDICTION_CONFIRMATION)).toBeInTheDocument();
    });
    expect(screen.queryByText(PREDICTION_DISCLAIMER)).not.toBeInTheDocument();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("shows confirmation when prediction already exists for card", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        items: [{ card_id: "card-1", prediction_text: PREDICTION_OPTIONS[1], logged_at: new Date().toISOString() }],
      }),
    });

    render(<PredictionLogger cardId="card-1" />);

    await waitFor(() => {
      expect(screen.getByText(PREDICTION_CONFIRMATION)).toBeInTheDocument();
    });
  });
});
