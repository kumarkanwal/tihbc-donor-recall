/** Poll only active API views when shared realtime is explicitly disabled. */
export function simulatorPollInterval(
  resource: "messages" | "conversations",
  active: boolean,
  source: "api" | "mock",
  realtime: boolean,
): number | false {
  if (!active || source !== "api" || realtime) return false;
  return resource === "messages" ? 3_000 : 10_000;
}
