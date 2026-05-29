import Link from "next/link";

import { Button } from "@/components/ui/button";

import { MirrorTopbar } from "./MirrorTopbar";

type MirrorSignInRequiredProps = {
  statusFilter?: string | null;
};

/** Shown when Mirror is opened without a Supabase session (server or client). */
export function MirrorSignInRequired({ statusFilter = null }: MirrorSignInRequiredProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      <MirrorTopbar status={statusFilter} onStatusChange={() => {}} />
      <div className="mx-auto w-full max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          The Mirror shows your prediction history and track record. Sign in with your tester
          account to continue.
        </p>
        <Button asChild className="mt-6">
          <Link href="/sign-in?next=/mirror">Sign in</Link>
        </Button>
      </div>
    </div>
  );
}
