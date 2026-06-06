import { resolveEditorialNavAccess } from "@/lib/admin-nav";

describe("resolveEditorialNavAccess", () => {
  it("hides editorial section for non-admin users", () => {
    const access = resolveEditorialNavAccess("user@example.com", "owner@example.com", "");
    expect(access.showEditorialSection).toBe(false);
  });

  it("shows editor links for ADMIN_EMAILS matches", () => {
    const access = resolveEditorialNavAccess(
      "owner@example.com",
      "owner@example.com",
      "",
    );
    expect(access.showEditorialSection).toBe(true);
    expect(access.showEditorQueue).toBe(true);
    expect(access.showWatchlist).toBe(true);
    expect(access.showSignalQueue).toBe(true);
    expect(access.showFactorDb).toBe(false);
  });

  it("shows factor db link for FACTOR_DB_ADMIN_EMAILS matches", () => {
    const access = resolveEditorialNavAccess(
      "owner@example.com",
      "",
      "owner@example.com",
    );
    expect(access.showEditorialSection).toBe(true);
    expect(access.showFactorDb).toBe(true);
    expect(access.showEditorQueue).toBe(false);
  });
});
