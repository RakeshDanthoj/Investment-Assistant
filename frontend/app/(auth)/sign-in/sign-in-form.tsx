"use client";

import { FormEvent, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
      <Alert className="border-finnwise-green/20 bg-green-50 text-finnwise-green">
        <AlertDescription>
          Check your inbox for <strong>{email}</strong>. The magic link expires in
          a few minutes.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email address</Label>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />
      </div>
      {errorMessage ? (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      ) : null}
      <Button type="submit" disabled={state === "loading"} className="w-full">
        {state === "loading" ? "Sending link…" : "Send magic link"}
      </Button>
    </form>
  );
}
