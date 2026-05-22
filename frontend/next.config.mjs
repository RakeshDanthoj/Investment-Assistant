import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));

/** Load monorepo root `.env.local` without `@next/env` (keeps Jest + pnpm happy). */
function loadRootEnvLocal() {
  const envPath = path.join(frontendDir, "..", ".env.local");
  if (!fs.existsSync(envPath)) return;
  const raw = fs.readFileSync(envPath, "utf8");
  for (const line of raw.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = val;
  }
}

loadRootEnvLocal();

function resolveSupabaseUrl(raw) {
  if (!raw) return "";
  if (raw.startsWith("http")) return raw.replace(/\/$/, "");
  return `https://${raw}.supabase.co`;
}

const supabaseUrl = resolveSupabaseUrl(process.env.SUPABASE_URL);
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY ?? "";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_SUPABASE_URL: supabaseUrl,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: supabaseAnonKey,
  },
};

export default nextConfig;
