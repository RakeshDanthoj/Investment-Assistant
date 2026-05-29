import Link from "next/link";
import { redirect } from "next/navigation";

import WatchlistClient from "./WatchlistClient";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { isEditorAdmin, normalizedEditorAdminEmailsFromEnv } from "@/lib/editor-admin";
import { createClient } from "@/lib/supabase/server";

export default async function EditorWatchlistPage() {
  const allowEnv = process.env.ADMIN_EMAILS ?? "";
  if (!normalizedEditorAdminEmailsFromEnv(allowEnv).length) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="font-serif text-2xl text-slate-900">Watchlist unavailable</h1>
        <p className="mt-3 text-slate-600">
          Set comma-separated Product Owner emails in <code>ADMIN_EMAILS</code> in the repo root{" "}
          <code>.env.local</code> (and the same list on the FastAPI service).
        </p>
      </main>
    );
  }

  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    redirect("/sign-in?next=/editor/watchlist");
  }

  const email = session.user.email;
  if (!isEditorAdmin(email, allowEnv)) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        <Alert variant="destructive">
          <AlertTitle>403 — Watchlist is restricted to editors.</AlertTitle>
          <AlertDescription>
            Signed in as {email ?? "unknown"}. Add your email to <code>ADMIN_EMAILS</code>.
          </AlertDescription>
        </Alert>
        <Link href="/pulse" className="mt-6 inline-block text-sm text-blue-800 underline">
          Back to the app
        </Link>
      </main>
    );
  }

  return <WatchlistClient accessToken={session.access_token} />;
}
