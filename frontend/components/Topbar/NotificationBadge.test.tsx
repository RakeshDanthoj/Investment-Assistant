/** @jest-environment jsdom */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { NotificationBadge } from "./NotificationBadge";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("../../lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: async () => ({
        data: {
          session: { access_token: "tok" },
        },
      }),
    },
  }),
}));

jest.mock("../../lib/api", () => ({
  getApiBaseUrl: () => "http://localhost:8000",
}));

describe("NotificationBadge", () => {
  beforeEach(() => {
    mockPush.mockClear();
    global.fetch = jest.fn();
  });

  it("renders pulsing dot when signal_fired notification exists and navigates to thread", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          {
            id: "n1",
            card_id: "card-uuid",
            kind: "signal_fired",
            payload: {},
            created_at: new Date().toISOString(),
          },
        ],
        count: 1,
      }),
    });

    render(<NotificationBadge />);

    await waitFor(() => {
      expect(screen.getByLabelText("Open thread for signal alert")).toBeInTheDocument();
    });

    const dot = document.querySelector(".animate-pulse");
    expect(dot).not.toBeNull();

    fireEvent.click(screen.getByLabelText("Open thread for signal alert"));
    expect(mockPush).toHaveBeenCalledWith("/thread/card-uuid");
  });

  it("renders nothing when no signal_fired items", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ items: [{ card_id: "c", kind: "card_published" }], count: 1 }),
    });

    const { container } = render(<NotificationBadge />);
    await waitFor(() => {
      expect(container.querySelector("button")).toBeNull();
    });
  });
});
