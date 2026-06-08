import { getApiBaseUrl } from "@/lib/api";

export type LocalDevSession = {
  access_token: string;
  refresh_token: string;
  expires_in?: number | null;
  token_type?: string;
};

export function isLocalDevHost(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const hostname = window.location.hostname;
  return hostname === "localhost" || hostname === "127.0.0.1";
}

export async function tryLocalDevLogin(
  email: string,
  password: string,
): Promise<LocalDevSession | null> {
  if (!isLocalDevHost()) {
    return null;
  }

  const endpoint = `${getApiBaseUrl().replace(/\/$/, "")}/api/auth/local-dev-login`;
  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), password }),
    });
  } catch {
    return null;
  }

  if (!response.ok) {
    return null;
  }

  const payload = (await response.json()) as LocalDevSession;
  if (!payload.access_token || !payload.refresh_token) {
    return null;
  }
  return payload;
}
