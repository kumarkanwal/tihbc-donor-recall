"use client";

import { X } from "lucide-react";

import { useToastStore } from "@/lib/toast/store";

/** Accessible application notifications anchored above persistent controls. */
export function ToastViewport(): React.JSX.Element {
  const messages = useToastStore((state) => state.messages);
  const dismiss = useToastStore((state) => state.dismiss);

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="fixed right-4 bottom-20 z-[80] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2"
    >
      {messages.map((message) => (
        <div
          key={message.id}
          role="status"
          className="border-border bg-surface shadow-surface rounded-card flex items-start gap-3 border p-4"
        >
          <div className="min-w-0 flex-1">
            <p className="font-medium">{message.title}</p>
            {message.description ? (
              <p className="text-muted-foreground mt-1 text-sm">
                {message.description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            aria-label="Dismiss notification"
            className="text-muted-foreground hover:text-foreground rounded p-1"
            onClick={() => dismiss(message.id)}
          >
            <X aria-hidden="true" className="size-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
