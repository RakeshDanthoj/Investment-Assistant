/** @jest-environment jsdom */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SignInForm from "./sign-in-form";

const mockPush = jest.fn();
const mockRefresh = jest.fn();
const mockSignInWithOtp = jest.fn();
const mockSignInWithPassword = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: mockRefresh,
  }),
}));

jest.mock("../../../lib/auth-redirect", () => ({
  buildAuthCallbackUrl: (next: string) => `http://localhost:3000/callback?next=${next}`,
}));

jest.mock("../../../lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      signInWithOtp: mockSignInWithOtp,
      signInWithPassword: mockSignInWithPassword,
    },
  }),
}));

describe("SignInForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSignInWithOtp.mockResolvedValue({ error: null });
    mockSignInWithPassword.mockResolvedValue({ error: null });
  });

  it("signs in with password and redirects", async () => {
    render(<SignInForm nextPath="/mirror" />);

    fireEvent.change(document.getElementById("password-email")!, {
      target: { value: "tester@finnwise.test" },
    });
    fireEvent.change(document.getElementById("password")!, {
      target: { value: "secret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in with password/i }));

    await waitFor(() => {
      expect(mockSignInWithPassword).toHaveBeenCalledWith({
        email: "tester@finnwise.test",
        password: "secret123",
      });
    });
    expect(mockPush).toHaveBeenCalledWith("/mirror");
    expect(mockRefresh).toHaveBeenCalled();
  });

  it("sends a magic link from the magic link tab", async () => {
    const user = userEvent.setup();
    render(<SignInForm nextPath="/pulse" />);

    await user.click(screen.getByRole("tab", { name: /magic link/i }));
    fireEvent.change(document.getElementById("magic-email")!, {
      target: { value: "tester@finnwise.test" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send magic link/i }));

    await waitFor(() => {
      expect(mockSignInWithOtp).toHaveBeenCalledWith({
        email: "tester@finnwise.test",
        options: {
          emailRedirectTo: "http://localhost:3000/callback?next=/pulse",
          shouldCreateUser: true,
        },
      });
    });
    expect(screen.getByText(/check your inbox/i)).toBeInTheDocument();
  });
});
