/** Canonical app origin for magic-link redirects (no trailing slash). */
export function resolveSiteOrigin(options?: {
  windowOrigin?: string;
  forwardedHost?: string | null;
  forwardedProto?: string | null;
}): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim().replace(/\/$/, "");
  if (configured) return configured;

  if (options?.forwardedHost) {
    const proto = (options.forwardedProto ?? "https").replace(/:$/, "");
    return `${proto}://${options.forwardedHost}`;
  }

  if (options?.windowOrigin) {
    return options.windowOrigin.replace(/\/$/, "");
  }

  const vercelUrl = process.env.VERCEL_URL?.trim();
  if (vercelUrl) return `https://${vercelUrl}`;

  return "";
}

export function buildAuthCallbackUrl(
  nextPath: string,
  options?: {
    windowOrigin?: string;
    forwardedHost?: string | null;
    forwardedProto?: string | null;
  },
): string {
  const origin = resolveSiteOrigin(options);
  if (!origin) {
    throw new Error("Could not resolve site origin for auth callback");
  }
  const next = nextPath.startsWith("/") ? nextPath : `/${nextPath}`;
  return `${origin}/callback?next=${encodeURIComponent(next)}`;
}
