import { redirect } from "next/navigation";

import { EmailPrefsForm } from "@/app/(app)/settings/email/_components/EmailPrefsForm";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";

export default async function EmailSettingsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/sign-in?next=/settings/email");
  }

  return (
    <main className="mx-auto max-w-lg p-6 md:p-10">
      <Card>
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold text-foreground">
            Email notifications
          </CardTitle>
          <CardDescription>
            Choose when FinnWise may email you. Messages are informational only — never buy, sell,
            or hold advice.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmailPrefsForm />
        </CardContent>
      </Card>
    </main>
  );
}
