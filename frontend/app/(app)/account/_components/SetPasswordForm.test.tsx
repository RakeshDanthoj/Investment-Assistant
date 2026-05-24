/** @jest-environment jsdom */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { SetPasswordForm } from "./SetPasswordForm";

const mockUpdateUser = jest.fn();

jest.mock("../../../../lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      updateUser: mockUpdateUser,
    },
  }),
}));

describe("SetPasswordForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUpdateUser.mockResolvedValue({ error: null });
  });

  it("saves a matching password", async () => {
    render(<SetPasswordForm />);

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "secret123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "secret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save password/i }));

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({ password: "secret123" });
    });
    expect(screen.getByText(/password saved/i)).toBeInTheDocument();
  });

  it("shows an error when passwords do not match", async () => {
    render(<SetPasswordForm />);

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "secret123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "different" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save password/i }));

    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
    expect(mockUpdateUser).not.toHaveBeenCalled();
  });
});
