/** Resolve Supabase URL from full URL or project ref (repo-root `.env.local`). */
export function resolveSupabaseUrl(raw?: string): string {
  const value =
    raw ??
    process.env.NEXT_PUBLIC_SUPABASE_URL ??
    process.env.SUPABASE_URL ??
    "";
  if (!value) return "";
  if (value.startsWith("http")) return value.replace(/\/$/, "");
  return `https://${value}.supabase.co`;
}

export function getSupabaseAnonKey(): string {
  return (
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    process.env.SUPABASE_ANON_KEY ??
    ""
  );
}
