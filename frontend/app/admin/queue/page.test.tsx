/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";

import { QueueEventsTable } from "./QueueEventsTable";

jest.mock("../../../lib/api", () => ({
  getApiBaseUrl: () => "http://localhost:8000",
  getLongRunningApiBaseUrl: () => "http://localhost:8000",
}));

describe("QueueEventsTable", () => {
  it("shows Open review when a draft card already exists", () => {
    render(
      <QueueEventsTable
        loading={false}
        rows={[
          {
            id: "event-1",
            title: "RBI holds repo rate",
            category: "rbi_policy",
            event_source: "rbi_rss",
            confidence_score: 82,
            lifecycle_state: "draft",
            canonical_url: "https://example.com/rbi",
            created_at: "2026-05-22T10:30:00.000Z",
            draft_card_id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
          },
        ]}
        generatingEventId={null}
        onGenerateDraft={jest.fn()}
      />,
    );

    const reviewLink = screen.getByRole("link", { name: "Open review" });
    expect(reviewLink).toHaveAttribute(
      "href",
      "/admin/review/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    );
    expect(screen.queryByRole("button", { name: "Generate draft" })).not.toBeInTheDocument();
  });

  it("calls onGenerateDraft when Generate draft is clicked", () => {
    const onGenerateDraft = jest.fn();

    render(
      <QueueEventsTable
        loading={false}
        rows={[
          {
            id: "event-2",
            title: "Budget headline",
            category: "budget",
            event_source: "newsapi",
            confidence_score: 55,
            lifecycle_state: "draft",
            canonical_url: "https://example.com/budget",
            created_at: "2026-05-22T08:00:00.000Z",
          },
        ]}
        generatingEventId={null}
        onGenerateDraft={onGenerateDraft}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Generate draft" }));
    expect(onGenerateDraft).toHaveBeenCalledWith("event-2");
  });

  it("shows generating state for the active row", () => {
    render(
      <QueueEventsTable
        loading={false}
        rows={[
          {
            id: "event-3",
            title: "Macro move",
            category: "macro",
            event_source: "newsapi",
            confidence_score: 70,
            lifecycle_state: "draft",
            canonical_url: "https://example.com/macro",
            created_at: "2026-05-22T09:00:00.000Z",
          },
        ]}
        generatingEventId="event-3"
        onGenerateDraft={jest.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Generating…" })).toBeDisabled();
  });
});

describe("requestDraftFromEvent", () => {
  it("posts event_id to the draft-from-event API", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ card_id: "card-new-1" }),
    });

    const { requestDraftFromEvent } = await import("../../../lib/editorial/draftFromEvent");
    const result = await requestDraftFromEvent("event-99");

    expect(result).toEqual({ ok: true, cardId: "card-new-1" });
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/cards/draft-from-event",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ event_id: "event-99", editor_notes: null }),
      }),
    );
  });
});
