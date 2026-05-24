"use client";

import Link from "next/link";
import { useState } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { getInitials } from "@/lib/user-display";

export type UserChipProps = {
  name: string;
  email: string;
  onSignOut: () => void | Promise<void>;
};

export default function UserChip({ name, email, onSignOut }: UserChipProps) {
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await onSignOut();
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div className="border-t border-border px-4 py-3">
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="h-auto w-full justify-start gap-2.5 px-1 py-1"
          >
            <Avatar size="sm" className="bg-primary text-[11px] font-bold text-primary-foreground">
              <AvatarFallback className="bg-primary text-[11px] font-bold text-primary-foreground">
                {getInitials(name)}
              </AvatarFallback>
            </Avatar>
            <span className="min-w-0 flex-1 text-left">
              <span className="block truncate text-[13px] font-medium text-foreground">
                {name}
              </span>
              <span className="block truncate font-mono text-[10px] text-muted-foreground">
                {email}
              </span>
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent side="top" align="start" className="w-[--radix-dropdown-menu-trigger-width]">
          <DropdownMenuItem asChild>
            <Link href="/account">Account</Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem disabled={signingOut} onClick={handleSignOut}>
            {signingOut ? "Signing out…" : "Sign out"}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
