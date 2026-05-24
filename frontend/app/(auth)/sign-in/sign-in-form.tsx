"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { buildAuthCallbackUrl } from "@/lib/auth-redirect";
import { createClient } from "@/lib/supabase/client";

type SignInFormProps = {
  nextPath: string;
};

type FormState = "idle" | "loading" | "sent" | "error";

export default function SignInForm({ nextPath }: SignInFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [magicLinkState, setMagicLinkState] = useState<FormState>("idle");
  const [passwordState, setPasswordState] = useState<FormState>("idle");
  const [magicLinkError, setMagicLinkError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function handleMagicLinkSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMagicLinkState("loading");
    setMagicLinkError(null);

    const supabase = createClient();
    const redirectTo = buildAuthCallbackUrl(nextPath, {
      windowOrigin: window.location.origin,
    });

    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: {
        emailRedirectTo: redirectTo,
        shouldCreateUser: true,
      },
    });

    if (error) {
      setMagicLinkState("error");
      setMagicLinkError(error.message);
      return;
    }

    setMagicLinkState("sent");
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordState("loading");
    setPasswordError(null);

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    if (error) {
      setPasswordState("error");
      setPasswordError(error.message);
      return;
    }

    setPasswordState("idle");
    router.push(nextPath);
    router.refresh();
  }

  if (magicLinkState === "sent") {
    return (
      <Alert className="border-finnwise-green/20 bg-green-50 text-finnwise-green">
        <AlertDescription>
          Check your inbox for <strong>{email}</strong>. The magic link expires in
          a few minutes. After your first sign-in, set a password under{" "}
          <strong>Account</strong> in the sidebar to skip magic links next time.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Tabs defaultValue="password" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="password">Password</TabsTrigger>
        <TabsTrigger value="magic-link">Magic link</TabsTrigger>
      </TabsList>

      <TabsContent value="password" className="mt-4">
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password-email">Email address</Label>
            <Input
              id="password-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Your account password"
            />
          </div>
          {passwordError ? (
            <Alert variant="destructive">
              <AlertDescription>{passwordError}</AlertDescription>
            </Alert>
          ) : null}
          <p className="text-xs text-muted-foreground">
            First time here? Use the magic link tab to verify your email, then set
            a password from <strong>Account</strong> in the sidebar.
          </p>
          <Button
            type="submit"
            disabled={passwordState === "loading"}
            className="w-full"
          >
            {passwordState === "loading" ? "Signing in…" : "Sign in with password"}
          </Button>
        </form>
      </TabsContent>

      <TabsContent value="magic-link" className="mt-4">
        <form onSubmit={handleMagicLinkSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="magic-email">Email address</Label>
            <Input
              id="magic-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </div>
          {magicLinkError ? (
            <Alert variant="destructive">
              <AlertDescription>{magicLinkError}</AlertDescription>
            </Alert>
          ) : null}
          <Button
            type="submit"
            disabled={magicLinkState === "loading"}
            className="w-full"
          >
            {magicLinkState === "loading" ? "Sending link…" : "Send magic link"}
          </Button>
        </form>
      </TabsContent>
    </Tabs>
  );
}
