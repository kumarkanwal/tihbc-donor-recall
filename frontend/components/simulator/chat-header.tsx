import Image from "next/image";
import { ArrowLeft, EllipsisVertical, Phone, Video } from "lucide-react";

interface ChatHeaderProps {
  isTyping: boolean;
  onBack: () => void;
}

/** Conversation header from the donor's perspective. */
export function ChatHeader({
  isTyping,
  onBack,
}: ChatHeaderProps): React.JSX.Element {
  return (
    <header className="bg-sim-header text-sim-header-text flex h-14 items-center gap-1 px-1.5">
      <button
        type="button"
        onClick={onBack}
        className="p-1.5"
        aria-label="Back to donor list"
      >
        <ArrowLeft aria-hidden="true" className="size-5" />
      </button>
      <span className="bg-sim-incoming flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-full p-1">
        <Image
          src="/images/IHHN-Logo-02-150x150.webp"
          alt=""
          width={28}
          height={28}
        />
      </span>
      <div className="min-w-0 flex-1 pl-1">
        <h3 className="truncate text-[0.72rem] font-semibold">
          Team Indus Health &amp; Blood Center
        </h3>
        <p className="text-[0.62rem] opacity-90">
          {isTyping ? "typing..." : "Business account"}
        </p>
      </div>
      <span
        className="flex items-center"
        aria-label="Call controls unavailable in simulator"
      >
        <Video aria-hidden="true" className="mx-1 size-4" />
        <Phone aria-hidden="true" className="mx-1 size-4" />
        <EllipsisVertical aria-hidden="true" className="mx-1 size-4" />
      </span>
    </header>
  );
}
