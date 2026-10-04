import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { components } from "@/lib/api/schema";

export type SessionUser = components["schemas"]["UserOut"];

interface SessionState {
  token: string | null;
  user: SessionUser | null;
  setSession: (token: string, user: SessionUser) => void;
  clearSession: () => void;
}

/** Demo-only browser session, held in memory and persisted for reloads. */
export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: (token, user) => set({ token, user }),
      clearSession: () => set({ token: null, user: null }),
    }),
    {
      name: "donor-recall-session",
      partialize: ({ token, user }) => ({ token, user }),
    },
  ),
);
