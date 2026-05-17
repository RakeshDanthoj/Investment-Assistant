import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { Step4ModeResult } from "./Step4ModeResult";

const mockPush = jest.fn();
const mockGetUser = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("../../../lib/supabase/client", () => ({
  createClient: () => ({
    auth: { getUser: mockGetUser },
  }),
}));

const result = {
  mode: "portfolio_protector",
  starting_surface: "pulse",
  rationale: "Invested across a few cycles.",
  session_id: "00000000-0000-0000-0000-000000000001",
  amount_echo: null,
};

describe("Step4ModeResult", () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockGetUser.mockReset();
  });

  it("routes signed-in users to /pulse", async () => {
    mockGetUser.mockResolvedValue({ data: { user: { id: "u1" } } });
    render(<Step4ModeResult result={result} />);

    const button = await screen.findByRole("button", { name: /go to the pulse/i });
    fireEvent.click(button);

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/pulse"));
  });

  it("routes signed-out users to sign-in with next=/pulse", async () => {
    mockGetUser.mockResolvedValue({ data: { user: null } });
    render(<Step4ModeResult result={result} />);

    const button = await screen.findByRole("button", {
      name: /sign in & open the pulse/i,
    });
    fireEvent.click(button);

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith("/sign-in?next=%2Fpulse"),
    );
  });

  describe("NEXT_PUBLIC_SKIP_AUTH", () => {
    const prev = process.env.NEXT_PUBLIC_SKIP_AUTH;
    beforeEach(() => {
      mockGetUser.mockClear();
      process.env.NEXT_PUBLIC_SKIP_AUTH = "true";
    });
    afterEach(() => {
      if (prev === undefined) delete process.env.NEXT_PUBLIC_SKIP_AUTH;
      else process.env.NEXT_PUBLIC_SKIP_AUTH = prev;
    });

    it("enters target surface without sign-in gate", async () => {
      render(<Step4ModeResult result={result} />);

      const button = await screen.findByRole("button", {
        name: /go to the pulse/i,
      });
      fireEvent.click(button);

      await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/pulse"));
      expect(mockGetUser).not.toHaveBeenCalled();
    });
  });
});
