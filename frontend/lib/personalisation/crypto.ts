/** Web Crypto helpers for session holdings seal + personalisation token (P2-S9). */

function textEncoder(): TextEncoder {
  return new TextEncoder();
}

function bytesToHex(bytes: ArrayBuffer): string {
  return Array.from(new Uint8Array(bytes))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function normalizeInstrumentId(instrumentId: string): string {
  return instrumentId.trim().toUpperCase();
}

export async function hmacSha256Hex(keyMaterial: string, message: string): Promise<string> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) {
    throw new Error("Web Crypto is not available in this environment.");
  }
  const key = await subtle.importKey(
    "raw",
    textEncoder().encode(keyMaterial),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await subtle.sign("HMAC", key, textEncoder().encode(message));
  return bytesToHex(sig);
}

export function getPersonalisationSalt(): string {
  const fromEnv = process.env.NEXT_PUBLIC_PERSONALISATION_TOKEN_SALT?.trim();
  return fromEnv || "dev-personalisation-salt-change-me";
}

export async function instrumentDigest(instrumentId: string, salt: string): Promise<string> {
  return hmacSha256Hex(salt, normalizeInstrumentId(instrumentId));
}

export async function buildPersonalisationToken(instrumentIds: string[]): Promise<string | null> {
  const unique = Array.from(
    new Set(instrumentIds.map(normalizeInstrumentId).filter(Boolean)),
  ).sort();
  if (!unique.length) return null;
  const salt = getPersonalisationSalt();
  const digests = await Promise.all(unique.map((id) => instrumentDigest(id, salt)));
  return `v1:${digests.sort().join(".")}`;
}
