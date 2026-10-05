import { describe, expect, it } from "vitest";
import { simulatorPollInterval } from "./refresh-policy";

describe("simulator refresh policy", () => {
  it("polls active API chats at 3s and the picker at 10s", () => {
    expect(simulatorPollInterval("messages", true, "api", false)).toBe(3000);
    expect(simulatorPollInterval("conversations", true, "api", false)).toBe(
      10000,
    );
  });
  it("never polls realtime, mock, or closed views", () => {
    for (const resource of ["messages", "conversations"] as const) {
      expect(simulatorPollInterval(resource, true, "api", true)).toBe(false);
      expect(simulatorPollInterval(resource, true, "mock", false)).toBe(false);
      expect(simulatorPollInterval(resource, false, "api", false)).toBe(false);
    }
  });
});
