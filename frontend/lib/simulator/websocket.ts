import { getAccessToken } from "@/lib/api/session";
import { env } from "@/lib/env";

import type { SimulatorEvent } from "./types";

const INITIAL_RECONNECT_MS = 1_000;
const MAX_RECONNECT_MS = 30_000;

function isSimulatorEvent(value: unknown): value is SimulatorEvent {
  if (!value || typeof value !== "object" || !("type" in value)) return false;
  const type = value.type;
  return (
    type === "message.created" ||
    type === "message.status_updated" ||
    type === "simulator.typing"
  );
}

/** Subscribe to documented simulator events with bounded reconnect backoff. */
export function subscribeToSimulatorEvents(
  listener: (event: SimulatorEvent) => void,
): () => void {
  if (typeof window === "undefined") return () => undefined;

  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectDelay = INITIAL_RECONNECT_MS;
  let closed = false;

  function connect(): void {
    const url = new URL(env.NEXT_PUBLIC_WS_URL);
    const token = getAccessToken();
    if (token) url.searchParams.set("token", token);
    socket = new WebSocket(url);
    socket.addEventListener("open", () => {
      reconnectDelay = INITIAL_RECONNECT_MS;
    });
    socket.addEventListener("message", ({ data }) => {
      if (typeof data !== "string") return;
      const candidate: unknown = JSON.parse(data);
      if (isSimulatorEvent(candidate)) listener(candidate);
    });
    socket.addEventListener("close", () => {
      if (closed) return;
      reconnectTimer = setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_MS);
    });
  }

  connect();
  return () => {
    closed = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    socket?.close();
  };
}
