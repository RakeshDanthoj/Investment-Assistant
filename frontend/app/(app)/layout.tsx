import { redirect } from "next/navigation";

import AppShell from "@/components/Sidebar/AppShell";
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

  if (!user) {
    redirect("/sign-in");
  }

  const userName = displayNameFromUser(user);
  const userEmail = user.email ?? "";

  return (
    <AppShell userName={userName} userEmail={userEmail}>
      {children}
    </AppShell>
  );
}
