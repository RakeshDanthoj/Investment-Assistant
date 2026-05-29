/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import MirrorPage from "./page";

jest.mock("../../../lib/supabase/server", () => ({
  createClient: jest.fn(async () => ({
    auth: { getSession: jest.fn(async () => ({ data: { session: null } })) },
  })),
}));

jest.mock("./MirrorContentSection", () => ({
  MirrorContentSection: function MockMirrorContentSection() {
    return (
      <div data-testid="mirror-client">
        <span>The Mirror</span>
        <span>Not what your portfolio is worth.</span>
      </div>
    );
  },
}));

describe("MirrorPage", () => {
  it("contains no rupee figures in the rendered subtree", async () => {
    const page = MirrorPage({ searchParams: {} });
    const { container } = render(page);
    expect(container.textContent).not.toMatch(/₹/);
    expect(screen.getByTestId("mirror-client")).toBeInTheDocument();
  });
});
