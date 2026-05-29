/** Product Owner emails for `/editor/*` routes — `ADMIN_EMAILS` in root `.env.local` (comma-separated). */

export function normalizedEditorAdminEmailsFromEnv(raw: string | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((p) => p.trim().toLowerCase())
    .filter(Boolean);
}

export function isEditorAdmin(email: string | null | undefined, rawList: string | undefined): boolean {
  const normalized = email?.trim().toLowerCase();
  if (!normalized) return false;
  return normalizedEditorAdminEmailsFromEnv(rawList).includes(normalized);
}
