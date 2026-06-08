import AppShell from "@/components/Sidebar/AppShell";
import { resolveEditorialNavAccess } from "@/lib/admin-nav";
import { QueryProvider } from "@/lib/perf/QueryProvider";
import { createClient } from "@/lib/supabase/server";
import { displayNameFromUser } from "@/lib/user-display";

export default async function AdminLayout({
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
  const editorialAccess = resolveEditorialNavAccess(
    user?.email ?? null,
    process.env.ADMIN_EMAILS,
    process.env.FACTOR_DB_ADMIN_EMAILS,
  );

  return (
    <QueryProvider>
      <AppShell
        userName={userName}
        userEmail={userEmail}
        editorialAccess={editorialAccess}
      >
        {children}
      </AppShell>
    </QueryProvider>
  );
}
