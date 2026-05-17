import { redirect } from "next/navigation";

import AppShell from "@/components/Sidebar/AppShell";
import { isAuthSkipped } from "@/lib/env";
import { createClient } from "@/lib/supabase/server";
import { displayNameFromUser } from "@/lib/user-display";

export default async function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!isAuthSkipped() && !user) {
    redirect("/sign-in");
  }

  const userName = user ? displayNameFromUser(user) : "Developer";
  const userEmail = user?.email ?? "dev@local";

  return (
    <AppShell userName={userName} userEmail={userEmail}>
      {children}
    </AppShell>
  );
}
