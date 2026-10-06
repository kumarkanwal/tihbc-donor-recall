import { BatteryMedium, Signal, Wifi } from "lucide-react";

import { useDemoNow } from "@/lib/demo-time";

export function formatPhoneTime(value: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Karachi",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(value);
}

/** Compact donor-phone status bar using simulator-only light tokens. */
export function SimulatorStatusBar(): React.JSX.Element {
  const demoNow = useDemoNow();
  return (
    <div className="bg-sim-incoming text-sim-text flex h-7 items-center justify-between px-5 text-[0.625rem] font-medium tabular-nums">
      <span>{demoNow ? formatPhoneTime(demoNow) : "--:--"}</span>
      <span className="flex items-center gap-1" aria-label="Phone connected">
        <Signal aria-hidden="true" className="size-3" />
        <Wifi aria-hidden="true" className="size-3" />
        <BatteryMedium aria-hidden="true" className="size-3.5" />
      </span>
    </div>
  );
}
