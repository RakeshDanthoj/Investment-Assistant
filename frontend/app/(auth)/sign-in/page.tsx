import SignInForm from "./sign-in-form";

type SignInPageProps = {
  searchParams?: { error?: string; next?: string };
};

export default function SignInPage({ searchParams }: SignInPageProps) {
  const authError = searchParams?.error === "auth";
  const nextPath = searchParams?.next ?? "/pulse";

  return (
    <main className="flex min-h-screen items-center justify-center bg-finnwise-surface p-8">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="font-display text-2xl font-bold text-slate-900">
          Sign in to FinnWise
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Enter your invited email. We&apos;ll send a one-time magic link — no
          password required.
        </p>
        {nextPath !== "/pulse" ? (
          <p className="mt-2 text-xs text-slate-400">
            After sign-in you&apos;ll open{" "}
            <span className="font-medium text-slate-600">{nextPath}</span>.
          </p>
        ) : (
          <p className="mt-2 text-xs text-slate-400">
            After sign-in you&apos;ll open{" "}
            <span className="font-medium text-slate-600">The Pulse</span>.
          </p>
        )}
        {authError ? (
          <p
            className="mt-4 rounded-md border border-finnwise-red/20 bg-red-50 px-3 py-2 text-sm text-finnwise-red"
            role="alert"
          >
            That sign-in link expired or was invalid. Request a new link below.
          </p>
        ) : null}
        <div className="mt-6">
          <SignInForm nextPath={nextPath} />
        </div>
      </div>
    </main>
  );
}
