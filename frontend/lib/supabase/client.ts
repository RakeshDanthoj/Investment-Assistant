import { createBrowserClient } from "@supabase/ssr";

import { getSupabaseAnonKey, resolveSupabaseUrl } from "@/lib/env";

export function createClient() {
  return createBrowserClient(resolveSupabaseUrl(), getSupabaseAnonKey());
}
