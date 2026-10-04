import { Check, CheckCheck } from "lucide-react";

import type { SimulatorMessageStatus } from "@/lib/simulator";
import { cn } from "@/lib/utils/class-names";

/** Donor-message delivery ticks, including blue read receipts. */
export function MessageTicks({
  status,
}: {
  status: SimulatorMessageStatus;
}): React.JSX.Element | null {
  if (status === "queued" || status === "failed") return null;
  const label =
    status === "read" ? "Read" : status === "delivered" ? "Delivered" : "Sent";
  const Icon = status === "sent" ? Check : CheckCheck;
  return (
    <span title={label} aria-label={label}>
      <Icon
        aria-hidden="true"
        className={cn("size-3.5", status === "read" && "text-sim-read")}
        strokeWidth={2}
      />
    </span>
  );
}
