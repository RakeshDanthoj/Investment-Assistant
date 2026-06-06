import { isEditorAdmin } from "@/lib/editor-admin";
import { isFactorDbAdmin } from "@/lib/factor-db-admin";

export type EditorialNavAccess = {
  showEditorialSection: boolean;
  showEditorQueue: boolean;
  showWatchlist: boolean;
  showSignalQueue: boolean;
  showFactorDb: boolean;
};

/** Resolve which editorial admin links may appear in the shell (UI only — routes stay server-gated). */
export function resolveEditorialNavAccess(
  email: string | null | undefined,
  adminEmails: string | undefined,
  factorDbEmails: string | undefined,
): EditorialNavAccess {
  const editor = isEditorAdmin(email, adminEmails);
  const factorDb = isFactorDbAdmin(email, factorDbEmails);
  return {
    showEditorQueue: editor,
    showWatchlist: editor,
    showSignalQueue: editor,
    showFactorDb: factorDb,
    showEditorialSection: editor || factorDb,
  };
}
