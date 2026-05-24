"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import HoldingsModal from "@/components/Holdings/HoldingsModal";
import { useSessionHoldings } from "@/lib/personalisation/useSessionHoldings";
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
  const [holdingsOpen, setHoldingsOpen] = useState(false);
  const { holdings, refresh } = useSessionHoldings();

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <>
      <UserChip
        name={userName}
        email={userEmail}
        holdingsCount={holdings.length}
        onManageHoldings={() => setHoldingsOpen(true)}
        onSignOut={handleSignOut}
      />
      <HoldingsModal
        open={holdingsOpen}
        onOpenChange={setHoldingsOpen}
        initialHoldings={holdings}
        onSaved={() => void refresh()}
      />
    </>
  );
}
