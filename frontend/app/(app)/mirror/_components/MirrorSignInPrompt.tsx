import Link from "next/link";

import { Button } from "@/components/ui/button";

/** Centered sign-in CTA for unsigned Mirror visitors (client-only). */
export function MirrorSignInPrompt() {
  return (
    <div className="mx-auto w-full max-w-lg px-4 py-16 text-center">
      <p className="text-sm text-muted-foreground">
        The Mirror shows your prediction history and track record. Sign in with your tester account
        to continue.
      </p>
      <Button asChild className="mt-6">
        <Link href="/sign-in?next=/mirror">Sign in</Link>
      </Button>
    </div>
  );
}
