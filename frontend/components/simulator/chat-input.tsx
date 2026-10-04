"use client";

import { Camera, CirclePlus, Send, Smile } from "lucide-react";
import { useState } from "react";

interface ChatInputProps {
  disabled?: boolean;
  onSend: (text: string) => void;
}

/** Donor text composer; accessory icons are intentionally decorative. */
export function ChatInput({
  disabled = false,
  onSend,
}: ChatInputProps): React.JSX.Element {
  const [text, setText] = useState("");

  function submit(): void {
    const value = text.trim();
    if (!value || disabled) return;
    onSend(value);
    setText("");
  }

  return (
    <div className="bg-sim-wallpaper flex items-center gap-1 p-2">
      <div className="bg-sim-incoming text-sim-secondary flex min-w-0 flex-1 items-center rounded-full px-2">
        <Smile aria-hidden="true" className="size-4 shrink-0" />
        <input
          aria-label="Message"
          placeholder="Message"
          value={text}
          disabled={disabled}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") submit();
          }}
          className="text-sim-text placeholder:text-sim-secondary min-w-0 flex-1 bg-transparent px-2 py-2 text-sm outline-none"
          dir="auto"
        />
        <CirclePlus aria-hidden="true" className="size-4 shrink-0" />
        <Camera aria-hidden="true" className="ml-2 size-4 shrink-0" />
      </div>
      {text.trim() ? (
        <button
          type="button"
          onClick={submit}
          disabled={disabled}
          className="bg-sim-header text-sim-header-text flex size-9 shrink-0 items-center justify-center rounded-full disabled:opacity-50"
          aria-label="Send message"
        >
          <Send aria-hidden="true" className="size-4" />
        </button>
      ) : null}
    </div>
  );
}
