"use client";

import { ChevronDown, LockKeyhole } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import type {
  SimulatorButton,
  SimulatorLanguage,
  SimulatorMessage,
} from "@/lib/simulator";
import {
  compareSimulatorMessages,
  effectiveMessageTime,
} from "@/lib/simulator/message-ordering";

import { DateSeparator } from "./date-separator";
import { SimulatorMessageBubble } from "./message-bubble";
import { TypingIndicator } from "./typing-indicator";

interface MessageListProps {
  messages: SimulatorMessage[];
  language: SimulatorLanguage;
  isTyping: boolean;
  onButtonReply: (message: SimulatorMessage, button: SimulatorButton) => void;
}

function timeLabel(value: string): string {
  return new Intl.DateTimeFormat("en-PK", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

/** Scroll-aware message history with grouped bubbles and unread jump affordance. */
export function MessageList({
  messages,
  language,
  isTyping,
  onButtonReply,
}: MessageListProps): React.JSX.Element {
  const orderedMessages = messages.slice().sort(compareSimulatorMessages);
  const messageCount = messages.length;
  const latestDonorReply = orderedMessages
    .filter(({ direction }) => direction === "inbound")
    .at(-1);
  const viewportRef = useRef<HTMLDivElement>(null);
  const [isNearBottom, setIsNearBottom] = useState(true);
  const [acknowledgedCount, setAcknowledgedCount] = useState(messageCount);
  const hasNewMessages = messageCount > acknowledgedCount && !isNearBottom;

  const scrollToBottom = useCallback((): void => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
    setIsNearBottom(true);
    setAcknowledgedCount(messageCount);
  }, [messageCount]);

  useEffect(() => {
    if (isNearBottom) scrollToBottom();
  }, [isNearBottom, scrollToBottom]);

  return (
    <div className="relative min-h-0 flex-1">
      <div
        ref={viewportRef}
        className="bg-sim-wallpaper h-full space-y-1.5 overflow-y-auto p-3"
        onScroll={(event) => {
          const element = event.currentTarget;
          setIsNearBottom(
            element.scrollHeight - element.scrollTop - element.clientHeight <
              48,
          );
        }}
      >
        <DateSeparator label="Today" />
        <div className="flex justify-center py-1">
          <div className="bg-sim-date-chip text-sim-date-text flex max-w-[88%] items-start gap-1 rounded-md px-2 py-1.5 text-center text-[0.6rem] shadow-sm">
            <LockKeyhole
              aria-hidden="true"
              className="mt-0.5 size-3 shrink-0"
            />
            This business uses a secure service to manage this chat.
          </div>
        </div>
        {orderedMessages.length === 0 ? (
          <p className="text-sim-secondary py-16 text-center text-xs">
            No messages in this conversation.
          </p>
        ) : null}
        {orderedMessages.map((message, index) => {
          const replied = orderedMessages.some(
            ({ reply_to_message_id }) => reply_to_message_id === message.id,
          );
          const predatesLatestReply = Boolean(
            latestDonorReply &&
            compareSimulatorMessages(message, latestDonorReply) < 0,
          );
          const previous = orderedMessages[index - 1];
          return (
            <SimulatorMessageBubble
              key={message.id}
              body={message.body}
              buttons={message.buttons ?? []}
              mediaType={message.media_type}
              mediaUrl={message.media_url}
              direction={
                message.direction === "outbound" ? "incoming" : "outgoing"
              }
              language={language}
              timestamp={timeLabel(effectiveMessageTime(message))}
              status={message.status}
              showTail={!previous || previous.direction !== message.direction}
              buttonsDisabled={replied || predatesLatestReply}
              onButtonReply={(button) => onButtonReply(message, button)}
            />
          );
        })}
        {isTyping ? <TypingIndicator /> : null}
      </div>
      {hasNewMessages ? (
        <button
          type="button"
          onClick={scrollToBottom}
          className="bg-sim-incoming text-sim-button absolute right-3 bottom-3 flex items-center gap-1 rounded-full px-3 py-1.5 text-xs shadow"
        >
          <ChevronDown aria-hidden="true" className="size-3" />
          New messages
        </button>
      ) : null}
    </div>
  );
}
