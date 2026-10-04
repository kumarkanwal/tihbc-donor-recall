/** Require the documented success body from a generated API response. */
export function requireResponseData<T>(
  data: T | undefined,
  description: string,
): T {
  if (!data) {
    throw new Error(`${description} response was empty.`);
  }
  return data;
}
