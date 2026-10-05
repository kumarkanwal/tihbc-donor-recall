import { cn } from "@/lib/utils/class-names";

export type ReportTab = "delivery" | "responses" | "inactive";

const tabs: Array<{ value: ReportTab; label: string }> = [
  { value: "delivery", label: "Delivery and engagement" },
  { value: "responses", label: "Responses" },
  { value: "inactive", label: "Inactive numbers" },
];

interface ReportTabsProps {
  value: ReportTab;
  onChange: (value: ReportTab) => void;
}

/** Accessible primary navigation for the three documented reports. */
export function ReportTabs({
  value,
  onChange,
}: ReportTabsProps): React.JSX.Element {
  return (
    <div className="border-border flex overflow-x-auto border-b" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          role="tab"
          aria-selected={value === tab.value}
          onClick={() => onChange(tab.value)}
          className={cn(
            "focus-visible:outline-ring border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap focus-visible:outline-2",
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
