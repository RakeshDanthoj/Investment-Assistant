/** Product Owner emails allowed to load `/admin/factor-db` — `FACTOR_DB_ADMIN_EMAILS` in root `.env.local` (comma-separated). */

export function normalizedAdminEmailsFromEnv(raw: string | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((p) => p.trim().toLowerCase())
    .filter(Boolean);
}

export function isFactorDbAdmin(email: string | null | undefined, rawList: string | undefined): boolean {
  const normalized = email?.trim().toLowerCase();
  if (!normalized) return false;
  const allow = normalizedAdminEmailsFromEnv(rawList);
  return allow.includes(normalized);
}
