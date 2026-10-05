import type { CampaignStatus } from "@/hooks/use-campaigns";
import { cn } from "@/lib/utils/class-names";

export type CampaignStatusFilter = CampaignStatus | "all";

const tabs: { value: CampaignStatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "running", label: "Running" },
  { value: "scheduled", label: "Scheduled" },
  { value: "paused", label: "Paused" },
  { value: "completed", label: "Completed" },
  { value: "draft", label: "Draft" },
];

/** Campaign status filter rendered as accessible tabs. */
export function CampaignStatusTabs({
  value,
  onChange,
}: {
  value: CampaignStatusFilter;
  onChange: (value: CampaignStatusFilter) => void;
}): React.JSX.Element {
  return (
    <div
      role="tablist"
      aria-label="Campaign status"
      className="border-border flex flex-wrap gap-1 border-b"
    >
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          role="tab"
          aria-selected={value === tab.value}
          onClick={() => onChange(tab.value)}
          className={cn(
            "focus-visible:outline-ring border-b-2 px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2",
            value === tab.value
              ? "border-primary text-primary"
              : "text-muted-foreground border-transparent",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
