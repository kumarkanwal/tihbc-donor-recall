import { afterEach, describe, expect, it, vi } from "vitest";

import { RealtimeClient } from "./client";

vi.mock("@/lib/env", () => ({
  env: { NEXT_PUBLIC_WS_URL: "ws://localhost:8000/ws" },
}));

type Listener = (event: { data?: unknown }) => void;

class FakeSocket {
  readonly listeners = new Map<string, Listener[]>();
  close = vi.fn();

  addEventListener(type: string, listener: Listener): void {
    const listeners = this.listeners.get(type) ?? [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  emit(type: string, event: { data?: unknown } = {}): void {
    for (const listener of this.listeners.get(type) ?? []) listener(event);
  }
}

describe("RealtimeClient", () => {
  afterEach(() => vi.useRealTimers());

  it("reconnects with exponential backoff capped by the client schedule", () => {
    vi.useFakeTimers();
    const sockets: FakeSocket[] = [];
    const client = new RealtimeClient({
      socketFactory: () => {
        const socket = new FakeSocket();
        sockets.push(socket);
        return socket as unknown as WebSocket;
      },
    });

    client.connect("access-token");
    expect(sockets).toHaveLength(1);
    sockets[0]?.emit("close");
    vi.advanceTimersByTime(999);
    expect(sockets).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(sockets).toHaveLength(2);
    sockets[1]?.emit("close");
    vi.advanceTimersByTime(1_999);
    expect(sockets).toHaveLength(2);
    vi.advanceTimersByTime(1);
    expect(sockets).toHaveLength(3);
    client.disconnect();
  });

  it("ignores unknown event types", () => {
    let socket: FakeSocket | undefined;
    const listener = vi.fn();
    const client = new RealtimeClient({
      socketFactory: () => {
        socket = new FakeSocket();
        return socket as unknown as WebSocket;
      },
    });
    client.subscribe(listener);
    client.connect("access-token");
    socket?.emit("message", {
      data: JSON.stringify({ type: "future.event", payload: {}, ts: "now" }),
    });
    expect(listener).not.toHaveBeenCalled();
    client.disconnect();
  });
});
