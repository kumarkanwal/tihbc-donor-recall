const accessTokenStorageKey = "tihbc_access_token";

function canUseBrowserStorage(): boolean {
  return typeof window !== "undefined";
}

/** Read the current access token when running in the browser. */
export function getAccessToken(): string | null {
  if (!canUseBrowserStorage()) {
    return null;
  }

  return window.localStorage.getItem(accessTokenStorageKey);
}

/** Persist an authenticated browser session token. */
export function setAccessToken(token: string): void {
  if (canUseBrowserStorage()) {
    window.localStorage.setItem(accessTokenStorageKey, token);
  }
}

/** Remove authentication state from browser storage. */
export function clearSession(): void {
  if (canUseBrowserStorage()) {
    window.localStorage.removeItem(accessTokenStorageKey);
  }
}

/** Clear an expired session and return the browser to login. */
export function clearSessionAndRedirect(): void {
  clearSession();

  if (canUseBrowserStorage() && window.location.pathname !== "/login") {
    // A hard navigation also clears authenticated in-memory state after token expiry.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login");
  }
}
