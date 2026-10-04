import type { SessionUser } from "@/lib/auth/session-store";
import { useSessionStore } from "@/lib/auth/session-store";

/** Read the current in-memory access token. */
export function getAccessToken(): string | null {
  return useSessionStore.getState().token;
}

/** Store a confirmed user and token in memory and demo browser storage. */
export function setSession(token: string, user: SessionUser): void {
  useSessionStore.getState().setSession(token, user);
}

/** Remove authentication state from memory and browser storage. */
export function clearSession(): void {
  useSessionStore.getState().clearSession();
  useSessionStore.persist.clearStorage();
}

/** Clear an expired session and return the browser to login. */
export function clearSessionAndRedirect(): void {
  clearSession();

  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    // A hard navigation also clears authenticated in-memory state after token expiry.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login");
  }
}
