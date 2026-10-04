"use client";

import { useEffect } from "react";

import {
  useOpenSimulatorConversation,
  useSendSimulatorReply,
  useSimulatorMessages,
} from "@/hooks/use-simulator";
import type {
  SimulatorButton,
  SimulatorConversation,
  SimulatorMessage,
} from "@/lib/simulator";

import { ChatHeader } from "./chat-header";
import { ChatInput } from "./chat-input";
import { MessageList } from "./message-list";

interface ConversationScreenProps {
  conversation: SimulatorConversation;
  onBack: () => void;
}

/** Live donor conversation backed by the selected simulator source. */
export function ConversationScreen({
  conversation,
  onBack,
}: ConversationScreenProps): React.JSX.Element {
  const donor = conversation.donor;
  const messages = useSimulatorMessages(donor.id);
  const openConversation = useOpenSimulatorConversation();
  const sendReply = useSendSimulatorReply(donor.id);

  useEffect(() => {
    openConversation.mutate(donor.id);
    // Open only when the selected donor changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [donor.id]);

  function sendButton(
    message: SimulatorMessage,
    button: SimulatorButton,
  ): void {
    sendReply.mutate({
      type: "button",
      button_id: button.id,
      reply_to_message_id: message.id,
    });
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ChatHeader isTyping={messages.isTyping} onBack={onBack} />
      {messages.isLoading ? (
        <div className="bg-sim-wallpaper flex flex-1 items-center justify-center">
          <span className="text-sim-secondary text-xs">
            Loading conversation...
          </span>
        </div>
      ) : null}
      {messages.isError ? (
        <div className="bg-sim-wallpaper text-sim-text flex flex-1 flex-col items-center justify-center p-6 text-center text-xs">
          <p>Messages could not be loaded.</p>
          <button
            type="button"
            className="text-sim-button mt-2 font-medium"
            onClick={() => void messages.refetch()}
          >
            Try again
          </button>
        </div>
      ) : null}
      {messages.data ? (
        <MessageList
          messages={messages.data}
          language={donor.language}
          isTyping={messages.isTyping}
          onButtonReply={sendButton}
        />
      ) : null}
      {sendReply.error ? (
        <p
          role="alert"
          className="bg-sim-incoming text-danger px-3 py-1 text-center text-[0.65rem]"
        >
          {sendReply.error.message}
        </p>
      ) : null}
      <ChatInput
        disabled={!donor.sim_reachable || sendReply.isPending}
        onSend={(text) => sendReply.mutate({ type: "text", text })}
      />
    </div>
  );
}
