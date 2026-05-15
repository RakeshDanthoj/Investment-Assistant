import HomePage from "./page";

jest.mock("next/navigation", () => ({
  redirect: jest.fn(),
}));

describe("HomePage", () => {
  it("redirects to onboarding", () => {
    const { redirect } = jest.requireMock("next/navigation");
    HomePage();
    expect(redirect).toHaveBeenCalledWith("/onboarding");
  });
});
