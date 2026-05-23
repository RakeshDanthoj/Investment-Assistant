/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import MirrorPage from "./page";

jest.mock("./_components/MirrorClient", () => ({
  __esModule: true,
  default: function MockMirrorClient() {
    return (
      <div data-testid="mirror-client">
        <span>The Mirror</span>
        <span>Not what your portfolio is worth.</span>
      </div>
    );
  },
}));

describe("MirrorPage", () => {
  it("contains no rupee figures in the rendered subtree", () => {
    const { container } = render(<MirrorPage />);
    expect(container.textContent).not.toMatch(/₹/);
    expect(screen.getByTestId("mirror-client")).toBeInTheDocument();
  });
});
