/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { MirrorContentSection } from "./MirrorContentSection";

jest.mock("../../../lib/supabase/server", () => ({
  createClient: jest.fn(async () => ({
    auth: { getSession: jest.fn(async () => ({ data: { session: null } })) },
  })),
}));

jest.mock("./_components/MirrorClient", () => ({
  __esModule: true,
  default: function MockMirrorClient({
    signedIn,
  }: {
    signedIn?: boolean;
    initialPayload?: unknown;
    initialStatusFilter?: string | null;
  }) {
    return (
      <div data-testid="mirror-client" data-signed-in={String(Boolean(signedIn))}>
        {signedIn ? "Signed in" : "Sign in with your tester account to continue."}
      </div>
    );
  },
}));

describe("MirrorContentSection", () => {
  it("renders MirrorClient with signedIn=false when there is no session", async () => {
    const section = await MirrorContentSection({ statusFilter: null });
    render(section);

    expect(screen.getByTestId("mirror-client")).toHaveAttribute("data-signed-in", "false");
    expect(screen.getByText(/Sign in with your tester account to continue/i)).toBeInTheDocument();
  });
});
