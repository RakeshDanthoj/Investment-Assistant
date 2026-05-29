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

  const userName = user ? displayNameFromUser(user) : "Guest";
  const userEmail = user?.email ?? "Not signed in";

  return (
    <AppShell userName={userName} userEmail={userEmail}>
      {children}
    </AppShell>
  );
}
