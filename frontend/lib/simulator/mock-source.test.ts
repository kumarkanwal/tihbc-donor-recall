import { afterEach, describe, expect, it, vi } from "vitest";

import { MockSimulatorSource } from "./mock-source";
import type { SimulatorEvent } from "./types";

afterEach(() => {
  vi.useRealTimers();
});

describe("MockSimulatorSource", () => {
  it("emits typing on and off around an automatic confirmation reply", async () => {
    vi.useFakeTimers();
    const source = new MockSimulatorSource();
    const events: SimulatorEvent[] = [];
    source.subscribe((event) => events.push(event));
    const [initial] = await source.listMessages("donor-aisha");

    await source.sendReply("donor-aisha", {
      type: "button",
      button_id: "btn_confirm",
      reply_to_message_id: initial.id,
    });

    expect(
      events.some(
        (event) => event.type === "simulator.typing" && event.payload.is_typing,
      ),
    ).toBe(true);

    await vi.advanceTimersByTimeAsync(1_500);

    const messages = await source.listMessages("donor-aisha");
    expect(messages).toHaveLength(3);
    expect(messages.at(-1)?.body).toContain("Thank you, Aisha Khan");
    expect(
      events.some(
        (event) =>
          event.type === "simulator.typing" && !event.payload.is_typing,
      ),
    ).toBe(true);
    expect(messages[1].status).toBe("read");
  });
});
