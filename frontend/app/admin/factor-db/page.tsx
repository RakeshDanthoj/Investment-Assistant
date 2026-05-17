import Link from "next/link";
import { redirect } from "next/navigation";

import FactorMatrix, { type SensitivityCell } from "./_components/FactorMatrix";

import { getApiBaseUrl } from "@/lib/api";
import { isFactorDbAdmin, normalizedAdminEmailsFromEnv } from "@/lib/factor-db-admin";
import { createClient } from "@/lib/supabase/server";

type ApiMatrixPayload = {
  sector: { slug: string; name: string };
  factors: { slug: string; display_name: string; sort_order: number }[];
  instruments: {
    id: string;
    ticker: string;
    display_name: string;
    isin?: string | null;
    exchange?: string | null;
  }[];
  sensitivities: Record<string, Record<string, SensitivityCell>>;
};

async function fetchMatrix(accessToken: string, sectorSlug: string): Promise<ApiMatrixPayload | null> {
  const qs = new URLSearchParams({ sector: sectorSlug });
  const endpoint = `${getApiBaseUrl()}/api/factor-db/matrix?${qs.toString()}`;
  let response: Response;
  try {
    response = await fetch(endpoint, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
  } catch {
    return null;
  }

  if (response.status === 403) return null;

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`factor-db matrix (${response.status}): ${text || response.statusText}`);
  }

  return (await response.json()) as ApiMatrixPayload;
}

export default async function FactorDbAdminPage({
  searchParams,
}: {
  searchParams?: { sector?: string };
}) {
  const allowEnv = process.env.FACTOR_DB_ADMIN_EMAILS ?? "";
  if (!normalizedAdminEmailsFromEnv(allowEnv).length) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="font-serif text-2xl text-slate-900">Factor DB viewer unavailable</h1>
        <p className="mt-3 text-slate-600">
          Set comma-separated Product Owner emails in <code>FACTOR_DB_ADMIN_EMAILS</code> in the
          repo root <code>.env.local</code> (and matching list on the API via{" "}
          <code>FACTOR_DB_ADMIN_EMAILS</code>).
        </p>
      </main>
    );
  }

  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    redirect("/sign-in?next=/admin/factor-db");
  }

  const email = session.user.email;
  if (!isFactorDbAdmin(email, allowEnv)) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        <p className="font-mono text-sm text-red-700">403 — Factor DB viewer is restricted.</p>
        <p className="mt-2 text-sm text-slate-600">
          Signed in as {email ?? "unknown"}. Ask the Product Owner to add your email to{" "}
          <code>FACTOR_DB_ADMIN_EMAILS</code>.
        </p>
        <Link href="/pulse" className="mt-6 inline-block text-sm text-blue-800 underline">
          Back to the app
        </Link>
      </main>
    );
  }

  const sectorSlug = (searchParams?.sector ?? "banking").trim().toLowerCase() || "banking";

  let data: ApiMatrixPayload;
  try {
    const fetched = await fetchMatrix(session.access_token, sectorSlug);
    if (fetched === null) {
      return (
        <main className="mx-auto max-w-3xl px-6 py-16">
          <p className="font-mono text-sm text-red-700">403 — API rejected Factor DB matrix access.</p>
          <p className="mt-2 text-sm text-slate-600">
            Ensure <code>FACTOR_DB_ADMIN_EMAILS</code> matches on the FastAPI service and reload.
          </p>
        </main>
      );
    }
    data = fetched;
  } catch (err) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="font-serif text-2xl text-slate-900">Could not load matrix</h1>
        <p className="mt-3 whitespace-pre-wrap text-sm text-red-700">
          {err instanceof Error ? err.message : "Unknown error"}
        </p>
      </main>
    );
  }

  const factorsSorted = [...data.factors].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <main className="mx-auto max-w-[1200px] px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">Internal · P1-S5</p>
          <h1 className="mt-2 font-serif text-3xl text-slate-950">Factor Exposure DB</h1>
          <p className="mt-2 max-w-xl text-sm text-slate-600">
            Banking sector slice with eight macro factors (PRD §7.1). Every cell is MMJ tagged with
            source URLs surfaced in Evidence.
          </p>
        </div>
      </header>

      <FactorMatrix
        sectorName={data.sector.name}
        factors={factorsSorted}
        instruments={data.instruments}
        sensitivities={data.sensitivities}
      />
    </main>
  );
}
