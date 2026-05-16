"use client";

import { useState } from "react";

import { getInitials } from "@/lib/user-display";

export type UserChipProps = {
  name: string;
  email: string;
  onSignOut: () => void | Promise<void>;
};

export default function UserChip({ name, email, onSignOut }: UserChipProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await onSignOut();
    } finally {
      setSigningOut(false);
      setMenuOpen(false);
    }
  }

  return (
    <div className="relative border-t border-slate-200 px-4 py-3">
      <button
        type="button"
        onClick={() => setMenuOpen((open) => !open)}
        className="flex w-full items-center gap-2.5 rounded-md px-1 py-1 text-left hover:bg-slate-100"
        aria-expanded={menuOpen}
        aria-haspopup="menu"
      >
        <span
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-finnwise-blue text-[11px] font-bold text-white"
          aria-hidden
        >
          {getInitials(name)}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] font-medium text-slate-900">
            {name}
          </span>
          <span className="block truncate font-mono text-[10px] text-slate-400">
            {email}
          </span>
        </span>
      </button>
      {menuOpen ? (
        <div
          role="menu"
          className="absolute bottom-full left-4 right-4 mb-1 rounded-md border border-slate-200 bg-white py-1 shadow-md"
        >
          <button
            type="button"
            role="menuitem"
            disabled={signingOut}
            onClick={handleSignOut}
            className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 disabled:opacity-60"
          >
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
