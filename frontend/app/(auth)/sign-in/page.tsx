import SignInForm from "./sign-in-form";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type SignInPageProps = {
  searchParams?: { error?: string; next?: string };
};

export default function SignInPage({ searchParams }: SignInPageProps) {
  const authError = searchParams?.error === "auth";
  const nextPath = searchParams?.next ?? "/pulse";

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold text-foreground">
            Sign in to FinnWise
          </CardTitle>
          <CardDescription>
            Returning testers: sign in with your password. First time? Use a magic
            link to verify your email, then set a password under Account.
          </CardDescription>
          {nextPath !== "/pulse" ? (
            <p className="text-xs text-muted-foreground">
              After sign-in you&apos;ll open{" "}
              <span className="font-medium text-foreground">{nextPath}</span>.
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              After sign-in you&apos;ll open{" "}
              <span className="font-medium text-foreground">The Pulse</span>.
            </p>
          )}
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {authError ? (
            <Alert variant="destructive">
              <AlertDescription>
                That sign-in link expired or was invalid. Request a new link below.
              </AlertDescription>
            </Alert>
          ) : null}
          <SignInForm nextPath={nextPath} />
        </CardContent>
      </Card>
    </main>
  );
}
