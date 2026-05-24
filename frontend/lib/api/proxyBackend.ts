import { getServerApiBaseUrl } from "@/lib/api/server";

const FORWARD_REQUEST_HEADERS = [
  "authorization",
  "content-type",
  "accept",
  "x-forwarded-for",
] as const;

const FORWARD_RESPONSE_HEADERS = ["content-type", "cache-control", "x-finnwise-timing"] as const;

function isLoopbackApiUrl(url: string): boolean {
  return /\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(url);
}

function hostsMatch(a: string, b: string): boolean {
  try {
    return new URL(a).host === new URL(b).host;
  } catch {
    return false;
  }
}

/** Proxy browser `/backend/...` requests to the configured FastAPI origin. */
export async function proxyToBackend(
  request: Request,
  pathSegments: string[],
): Promise<Response> {
  const configured = getServerApiBaseUrl().replace(/\/$/, "");
  if (!configured || isLoopbackApiUrl(configured)) {
    return Response.json(
      {
        detail:
          "API proxy is not configured. Set NEXT_PUBLIC_API_BASE_URL on Vercel to your live backend URL, then redeploy.",
      },
      { status: 503 },
    );
  }

  const incoming = new URL(request.url);
  if (hostsMatch(configured, incoming.href)) {
    return Response.json(
      {
        detail:
          "NEXT_PUBLIC_API_BASE_URL must be your Render (or API) origin, not this Vercel frontend URL. " +
          "Example: https://finnwise-backend.onrender.com",
      },
      { status: 503 },
    );
  }
  const path = pathSegments.map((segment) => encodeURIComponent(segment)).join("/");
  const target = `${configured}/${path}${incoming.search}`;

  const headers = new Headers();
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });
  } catch {
    return Response.json(
      {
        detail:
          "Could not reach the API backend. Confirm the Render service is running and NEXT_PUBLIC_API_BASE_URL is correct.",
      },
      { status: 503 },
    );
  }

  const responseHeaders = new Headers();
  for (const name of FORWARD_RESPONSE_HEADERS) {
    const value = backendRes.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }

  return new Response(backendRes.body, {
    status: backendRes.status,
    headers: responseHeaders,
  });
}
