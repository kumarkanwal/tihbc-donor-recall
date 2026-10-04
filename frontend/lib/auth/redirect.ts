/** Keep post-login redirects inside this application. */
export function getSafeRedirectPath(requestedPath?: string): string {
  if (!requestedPath?.startsWith("/") || requestedPath.startsWith("//")) {
    return "/";
  }

  return requestedPath;
}
