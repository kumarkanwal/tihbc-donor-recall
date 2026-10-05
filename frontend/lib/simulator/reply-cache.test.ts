import { expect, it } from "vitest";
import { createMockSeed } from "./mock-data";
import {
  optimisticReply,
  updateReplyCache,
  type MessageHistory,
} from "./reply-cache";

it("shows a localized optimistic donor reply and reconciles without duplicates", () => {
  const message = createMockSeed().conversations[0].last_message;
  const history: MessageHistory = {
    pages: [{ items: [message], next_before: null, limit: 50 }],
    pageParams: [undefined],
  };
  const optimistic = optimisticReply(
    message.donor_id,
    {
      type: "button",
      button_id: "btn_confirm",
      reply_to_message_id: message.id,
    },
    history,
  );
  expect(optimistic.body).toBe("Confirm");
  expect(optimistic.reply_to_message_id).toBe(message.id);
  const appended = updateReplyCache(history, optimistic.id, optimistic);
  expect(appended?.pages[0].items).toHaveLength(2);
  const saved = { ...optimistic, id: "saved", status: "delivered" as const };
  const reconciled = updateReplyCache(appended, optimistic.id, saved);
  expect(reconciled?.pages[0].items.at(-1)).toEqual(saved);
  expect(
    updateReplyCache(reconciled, optimistic.id, saved)?.pages[0].items,
  ).toHaveLength(2);
  expect(updateReplyCache(appended, optimistic.id)?.pages[0].items).toEqual([
    message,
  ]);
});
