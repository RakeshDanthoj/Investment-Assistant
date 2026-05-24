import { redirect } from "next/navigation";

import { SetPasswordForm } from "@/app/(app)/account/_components/SetPasswordForm";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";

export default async function AccountPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/sign-in?next=/account");
  }

  return (
    <main className="mx-auto max-w-lg p-6 md:p-10">
      <Card>
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold text-foreground">
            Account
          </CardTitle>
          <CardDescription>
            Signed in as <span className="font-medium text-foreground">{user.email}</span>.
            Set a password so you can sign in without requesting another magic link.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SetPasswordForm />
        </CardContent>
      </Card>
    </main>
  );
}
