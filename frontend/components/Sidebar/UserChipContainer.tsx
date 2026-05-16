"use client";

import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

import UserChip from "./UserChip";

type UserChipContainerProps = {
  userName: string;
  userEmail: string;
};

export default function UserChipContainer({
  userName,
  userEmail,
}: UserChipContainerProps) {
  const router = useRouter();

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <UserChip name={userName} email={userEmail} onSignOut={handleSignOut} />
  );
}
