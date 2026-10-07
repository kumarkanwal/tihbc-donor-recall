import type { SimulatorButton, SimulatorMessageStatus } from "@/lib/simulator";
import { cn } from "@/lib/utils/class-names";
import {
  parseWhatsAppFormat,
  splitBidiText,
} from "@/lib/utils/whatsapp-format";

import { MediaHeader } from "./media-header";
import { MessageTicks } from "./message-ticks";
import { QuickReplyButtons } from "./quick-reply-buttons";

interface SimulatorMessageBubbleProps {
  body: string;
  buttons?: SimulatorButton[];
  mediaType?: "none" | "image" | "video";
  mediaUrl?: string | null;
  direction?: "incoming" | "outgoing";
  language?: "en" | "ur";
  timestamp?: string;
  status?: SimulatorMessageStatus;
  showTail?: boolean;
  buttonsDisabled?: boolean;
  onButtonReply?: (button: SimulatorButton) => void;
}

function IsolatedText({
  value,
  isolateLatin,
}: {
  value: string;
  isolateLatin: boolean;
}): React.JSX.Element {
  if (!isolateLatin) return <>{value}</>;
  return (
    <>
      {splitBidiText(value).map((segment, index) =>
        segment.isolate ? (
          <bdi key={index} dir="ltr">
            {segment.value}
          </bdi>
        ) : (
          <span key={index}>{segment.value}</span>
        ),
      )}
    </>
  );
}

function FormattedBody({
  body,
  language,
}: {
  body: string;
  language: "en" | "ur";
}): React.JSX.Element {
  return (
    <p
      className={cn("whitespace-pre-wrap", language === "ur" && "font-urdu")}
      lang={language}
      dir={language === "ur" ? "rtl" : "ltr"}
    >
      {parseWhatsAppFormat(body).map((token, index) => {
        const key = `${token.kind}-${index}`;
        if (token.kind === "bold")
          return (
            <strong key={key}>
              <IsolatedText
                value={token.value}
                isolateLatin={language === "ur"}
              />
            </strong>
          );
        if (token.kind === "italic")
          return (
            <em key={key}>
              <IsolatedText
                value={token.value}
                isolateLatin={language === "ur"}
              />
            </em>
          );
        return (
          <span key={key}>
            <IsolatedText
              value={token.value}
              isolateLatin={language === "ur"}
            />
          </span>
        );
      })}
    </p>
  );
}

/** WhatsApp-styled bubble shared by series previews and live donor chats. */
export function SimulatorMessageBubble({
  body,
  buttons = [],
  mediaType = "none",
  mediaUrl,
  direction = "incoming",
  language = "en",
  timestamp = "10:30 AM",
  status = "delivered",
  showTail = false,
  buttonsDisabled = false,
  onButtonReply,
}: SimulatorMessageBubbleProps): React.JSX.Element {
  const outgoing = direction === "outgoing";
  return (
    <div className={cn("flex", outgoing ? "justify-end" : "justify-start")}>
      <article
        data-testid="simulator-message"
        className={cn(
          "text-sim-text relative max-w-[80%] rounded-[7.5px] text-[14.2px] shadow-sm",
          outgoing ? "bg-sim-outgoing" : "bg-sim-incoming",
          showTail &&
            (outgoing
              ? "before:bg-sim-outgoing before:absolute before:top-1 before:-right-1 before:size-2 before:rotate-45"
              : "before:bg-sim-incoming before:absolute before:top-1 before:-left-1 before:size-2 before:rotate-45"),
        )}
      >
        <div className="relative p-2 pb-1">
          <MediaHeader mediaType={mediaType} mediaUrl={mediaUrl} />
          <FormattedBody body={body} language={language} />
          <span
            className="text-sim-secondary mt-1 flex items-center justify-end gap-0.5 font-sans text-[0.62rem] leading-none tabular-nums"
            lang="en"
            dir="ltr"
          >
            {timestamp}
            {outgoing ? <MessageTicks status={status} /> : null}
          </span>
        </div>
        <QuickReplyButtons
          buttons={buttons}
          disabled={buttonsDisabled}
          onReply={onButtonReply}
        />
      </article>
    </div>
  );
}
