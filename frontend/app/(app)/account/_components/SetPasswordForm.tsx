"use client";

import { FormEvent, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

const MIN_PASSWORD_LENGTH = 6;

type FormState = "idle" | "loading" | "success" | "error";

export function SetPasswordForm() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [state, setState] = useState<FormState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (password.length < MIN_PASSWORD_LENGTH) {
      setState("error");
      setErrorMessage(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }

    if (password !== confirmPassword) {
      setState("error");
      setErrorMessage("Passwords do not match.");
      return;
    }

    setState("loading");

    const supabase = createClient();
    const { error } = await supabase.auth.updateUser({ password });

    if (error) {
      setState("error");
      setErrorMessage(error.message);
      return;
    }

    setState("success");
    setPassword("");
    setConfirmPassword("");
  }

  if (state === "success") {
    return (
      <Alert className="border-finnwise-green/20 bg-green-50 text-finnwise-green">
        <AlertDescription>
          Password saved. Next time, sign in with the <strong>Password</strong> tab
          on the sign-in page — no magic link needed.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="new-password">New password</Label>
        <Input
          id="new-password"
          name="new-password"
          type="password"
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD_LENGTH}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="At least 6 characters"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="confirm-password">Confirm password</Label>
        <Input
          id="confirm-password"
          name="confirm-password"
          type="password"
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD_LENGTH}
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          placeholder="Repeat password"
        />
      </div>
      {errorMessage ? (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      ) : null}
      <Button type="submit" disabled={state === "loading"} className="w-full max-w-xs">
        {state === "loading" ? "Saving…" : "Save password"}
      </Button>
    </form>
  );
}
