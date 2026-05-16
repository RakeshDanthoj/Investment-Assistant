"use client";

import { FormEvent, useState } from "react";

import { createClient } from "@/lib/supabase/client";

type SignInFormProps = {
  nextPath: string;
};

type FormState = "idle" | "loading" | "sent" | "error";

export default function SignInForm({ nextPath }: SignInFormProps) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<FormState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setErrorMessage(null);

    const supabase = createClient();
    const redirectTo = `${window.location.origin}/callback?next=${encodeURIComponent(nextPath)}`;

    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: {
        emailRedirectTo: redirectTo,
        shouldCreateUser: true,
      },
    });

    if (error) {
      setState("error");
      setErrorMessage(error.message);
      return;
    }

    setState("sent");
  }

  if (state === "sent") {
    return (
      <div
        className="rounded-md border border-finnwise-green/20 bg-green-50 px-4 py-3 text-sm text-finnwise-green"
        role="status"
      >
        Check your inbox for <strong>{email}</strong>. The magic link expires in
        a few minutes.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-slate-700"
        >
          Email address
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none ring-finnwise-blue focus:border-finnwise-blue focus:ring-2"
        />
      </div>
      {errorMessage ? (
        <p className="text-sm text-finnwise-red" role="alert">
          {errorMessage}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={state === "loading"}
        className="w-full rounded-md bg-finnwise-blue px-4 py-2.5 text-sm font-medium text-white transition hover:bg-finnwise-blue/90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {state === "loading" ? "Sending link…" : "Send magic link"}
      </button>
    </form>
  );
}
