import type { InfiniteData } from "@tanstack/react-query";
import type {
  SimulatorMessage,
  SimulatorMessagePage,
  SimulatorReply,
} from "./types";

export type MessageHistory = InfiniteData<
  SimulatorMessagePage,
  string | undefined
>;

/** Add or reconcile one reply without dropping older pages or concurrent events. */
export function updateReplyCache(
  history: MessageHistory | undefined,
  optimisticId: string,
  message?: SimulatorMessage,
): MessageHistory | undefined {
  if (!history) return history;
  return {
    ...history,
    pages: history.pages.map((page, index) => ({
      ...page,
      items: [
        ...page.items.filter(
          ({ id }) => id !== optimisticId && id !== message?.id,
        ),
        ...(index === 0 && message ? [message] : []),
      ],
    })),
  };
}

/** Donor bubble only; automatic TIHBC replies are never fabricated in API mode. */
export function optimisticReply(
  donorId: string,
  request: SimulatorReply,
  history?: MessageHistory,
): SimulatorMessage {
  const timestamp = new Date().toISOString();
  const latest = history?.pages[0]?.items;
  const source =
    request.type === "button"
      ? history?.pages
          .flatMap((page) => page.items)
          .find(({ id }) => id === request.reply_to_message_id)
      : latest?.filter(({ direction }) => direction === "outbound").at(-1);
  return {
    id: `optimistic-${crypto.randomUUID()}`,
    donor_id: donorId,
    direction: "inbound",
    kind: request.type === "button" ? "button_reply" : "text",
    body:
      request.type === "text"
        ? request.text
        : (source?.buttons?.find(({ id }) => id === request.button_id)?.label ??
          request.button_id),
    media_type: "none",
    media_url: null,
    buttons: null,
    button_id: request.type === "button" ? request.button_id : null,
    reply_to_message_id: source?.id ?? null,
    status: "sent",
    scheduled_at: timestamp,
    created_at: timestamp,
    sent_at: null,
    delivered_at: null,
    read_at: null,
  };
}
