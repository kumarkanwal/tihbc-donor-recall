/** Convert the documented versioned API URL to the generated client's base. */
export function getGeneratedClientBaseUrl(apiUrl: string): string {
  const url = new URL(apiUrl);
  url.pathname = url.pathname.replace(/\/api\/v1\/?$/, "");
  return url.toString().replace(/\/$/, "");
}
