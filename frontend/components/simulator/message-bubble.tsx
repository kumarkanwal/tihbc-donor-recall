import Image from "next/image";

import { cn } from "@/lib/utils/class-names";

interface SimulatorMessageBubbleProps {
  body: string;
  buttons?: { id: string; label: string }[];
  mediaType?: "none" | "image" | "video";
  mediaUrl?: string | null;
  direction?: "incoming" | "outgoing";
  language?: "en" | "ur";
  timestamp?: string;
}

function MessageMedia({
  mediaType,
  mediaUrl,
}: Pick<
  SimulatorMessageBubbleProps,
  "mediaType" | "mediaUrl"
>): React.JSX.Element | null {
  if (!mediaUrl || mediaType === "none") return null;
  if (mediaType === "video") {
    return (
      <video
        src={mediaUrl}
        controls
        className="mb-2 aspect-video w-full rounded object-cover"
      />
    );
  }
  return (
    <Image
      src={mediaUrl}
      alt="Message attachment"
      width={320}
      height={180}
      unoptimized
      className="mb-2 aspect-video w-full rounded object-cover"
    />
  );
}

/** WhatsApp-styled message bubble shared by preview and future live chats. */
export function SimulatorMessageBubble({
  body,
  buttons = [],
  mediaType = "none",
  mediaUrl,
  direction = "incoming",
  language = "en",
  timestamp = "10:30 AM",
}: SimulatorMessageBubbleProps): React.JSX.Element {
  return (
    <div
      className={cn(
        "flex",
        direction === "outgoing" ? "justify-end" : "justify-start",
      )}
    >
      <article
        className={cn(
          "text-sim-text max-w-[80%] overflow-hidden rounded-[7.5px] text-[14.2px] shadow-sm",
          direction === "outgoing" ? "bg-sim-outgoing" : "bg-sim-incoming",
        )}
      >
        <div
          className="p-2 pb-1"
          lang={language}
          dir={language === "ur" ? "rtl" : "ltr"}
        >
          <MessageMedia mediaType={mediaType} mediaUrl={mediaUrl} />
          <p className="whitespace-pre-wrap">{body}</p>
          <p className="text-sim-secondary mt-1 text-right font-sans text-[0.62rem] leading-none tabular-nums">
            {timestamp}
          </p>
        </div>
        {buttons.length > 0 ? (
          <div className="border-sim-secondary/20 border-t">
            {buttons.map((button) => (
              <div
                key={button.id}
                className="text-sim-button border-sim-secondary/20 border-b px-3 py-2 text-center text-xs font-medium last:border-b-0"
              >
                {button.label}
              </div>
            ))}
          </div>
        ) : null}
      </article>
    </div>
  );
}
