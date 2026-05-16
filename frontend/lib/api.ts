/** Backend origin for browser-side fetch — set NEXT_PUBLIC_API_BASE_URL in `.env.local`. */
export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}
