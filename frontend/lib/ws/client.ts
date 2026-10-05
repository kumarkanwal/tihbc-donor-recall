import { env } from "@/lib/env";

import { parseRealtimeEvent, type RealtimeEvent } from "./events";

const INITIAL_RECONNECT_MS = 1_000;
const MAX_RECONNECT_MS = 30_000;

type EventListener = (event: RealtimeEvent) => void;
type ReconnectListener = () => void;
type SocketFactory = (url: string) => WebSocket;

interface RealtimeClientOptions {
  socketFactory?: SocketFactory;
  setTimer?: typeof setTimeout;
  clearTimer?: typeof clearTimeout;
}

/** One tab-scoped authenticated WebSocket with bounded reconnect behavior. */
export class RealtimeClient {
  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = INITIAL_RECONNECT_MS;
  private token: string | null = null;
  private hasOpened = false;
  private readonly listeners = new Set<EventListener>();
  private readonly reconnectListeners = new Set<ReconnectListener>();
  private readonly socketFactory: SocketFactory;
  private readonly setTimer: typeof setTimeout;
  private readonly clearTimer: typeof clearTimeout;

  constructor(options: RealtimeClientOptions = {}) {
    this.socketFactory = options.socketFactory ?? ((url) => new WebSocket(url));
    this.setTimer = options.setTimer ?? setTimeout;
    this.clearTimer = options.clearTimer ?? clearTimeout;
  }

  connect(token: string): void {
    if (this.token === token && this.socket) return;
    this.disconnect();
    this.token = token;
    this.open();
  }

  disconnect(): void {
    this.token = null;
    this.hasOpened = false;
    this.reconnectDelay = INITIAL_RECONNECT_MS;
    if (this.reconnectTimer) this.clearTimer(this.reconnectTimer);
    this.reconnectTimer = null;
    const socket = this.socket;
    this.socket = null;
    socket?.close();
  }

  subscribe(listener: EventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onReconnect(listener: ReconnectListener): () => void {
    this.reconnectListeners.add(listener);
    return () => this.reconnectListeners.delete(listener);
  }

  private open(): void {
    if (!this.token) return;
    const url = new URL(env.NEXT_PUBLIC_WS_URL);
    url.searchParams.set("token", this.token);
    const socket = this.socketFactory(url.toString());
    this.socket = socket;
    socket.addEventListener("open", () => {
      const reconnected = this.hasOpened;
      this.hasOpened = true;
      this.reconnectDelay = INITIAL_RECONNECT_MS;
      if (reconnected) {
        for (const listener of this.reconnectListeners) listener();
      }
    });
    socket.addEventListener("message", ({ data }) => this.receive(data));
    socket.addEventListener("close", () => {
      if (this.socket === socket) this.socket = null;
      if (!this.token) return;
      const delay = this.reconnectDelay;
      this.reconnectDelay = Math.min(delay * 2, MAX_RECONNECT_MS);
      this.reconnectTimer = this.setTimer(() => this.open(), delay);
    });
  }

  private receive(data: unknown): void {
    if (typeof data !== "string") return;
    try {
      const event = parseRealtimeEvent(JSON.parse(data) as unknown);
      if (!event) return;
      for (const listener of this.listeners) listener(event);
    } catch (error: unknown) {
      if (!(error instanceof SyntaxError)) throw error;
    }
  }
}

export const realtimeClient = new RealtimeClient();
