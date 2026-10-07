import type { SimulatorMessage } from "./types";

/** Resolve the timestamp used to order and label a conversation message. */
export function effectiveMessageTime(message: SimulatorMessage): string {
  return message.sent_at ?? message.created_at ?? message.scheduled_at;
}

/** Sort messages chronologically with a stable UUID tie-breaker. */
export function compareSimulatorMessages(
  left: SimulatorMessage,
  right: SimulatorMessage,
): number {
  const timeDifference =
    new Date(effectiveMessageTime(left)).getTime() -
    new Date(effectiveMessageTime(right)).getTime();
  return timeDifference || left.id.localeCompare(right.id);
}
