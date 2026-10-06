import { MaskedPhone } from "@/components/shared/masked-phone";
import type { SimulatorConversation } from "@/lib/simulator";
import { cn } from "@/lib/utils/class-names";

function initials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toLocaleUpperCase();
}

function messageTime(value?: string): string {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-PK", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

/** One donor row in the phone's conversation picker. */
export function ChatListItem({
  conversation,
  onSelect,
}: {
  conversation: SimulatorConversation;
  onSelect: () => void;
}): React.JSX.Element {
  const {
    donor,
    last_message: lastMessage,
    unread_count: unreadCount,
  } = conversation;
  return (
    <button
      type="button"
      data-testid="simulator-conversation-row"
      data-donor-name={donor.name}
      onClick={onSelect}
      className={cn(
        "border-sim-secondary/15 flex w-full items-center gap-2 border-b px-3 py-2 text-left focus-visible:outline-2 focus-visible:outline-offset-[-2px]",
        donor.sim_reachable ? "bg-sim-incoming" : "bg-sim-wallpaper opacity-60",
      )}
    >
      <span className="bg-sim-header text-sim-header-text flex size-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold">
        {initials(donor.name)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center justify-between gap-2">
          <span
            className={cn(
              "truncate text-xs font-semibold",
              donor.language === "ur" && "font-urdu",
            )}
            dir="auto"
          >
            {donor.name}
          </span>
          <span className="text-sim-secondary shrink-0 text-[0.58rem] tabular-nums">
            {messageTime(lastMessage?.created_at)}
          </span>
        </span>
        <span className="text-sim-secondary mt-0.5 flex min-w-0 items-center justify-between gap-1 text-[0.65rem]">
          <span className="min-w-0 truncate">
            {donor.sim_reachable ? lastMessage?.body : "Number not on WhatsApp"}
          </span>
          {unreadCount > 0 ? (
            <span className="bg-sim-button text-sim-header-text flex size-4 shrink-0 items-center justify-center rounded-full text-[0.55rem]">
              {unreadCount}
            </span>
          ) : null}
        </span>
        <span className="text-sim-secondary text-[0.58rem]">
          {donor.campaign_name ? `${donor.campaign_name} · ` : null}
          <MaskedPhone value={donor.phone} />
        </span>
      </span>
    </button>
  );
}
