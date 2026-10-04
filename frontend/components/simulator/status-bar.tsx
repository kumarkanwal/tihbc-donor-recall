import { BatteryMedium, Signal, Wifi } from "lucide-react";

/** Compact donor-phone status bar using simulator-only light tokens. */
export function SimulatorStatusBar(): React.JSX.Element {
  return (
    <div className="bg-sim-incoming text-sim-text flex h-7 items-center justify-between px-5 text-[0.625rem] font-medium tabular-nums">
      <span>10:30</span>
      <span className="flex items-center gap-1" aria-label="Phone connected">
        <Signal aria-hidden="true" className="size-3" />
        <Wifi aria-hidden="true" className="size-3" />
        <BatteryMedium aria-hidden="true" className="size-3.5" />
      </span>
    </div>
  );
}
