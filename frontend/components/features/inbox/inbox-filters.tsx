import { Input } from "@/components/ui/input";
import type {
  FollowUpStatus,
  FollowUpSummary,
  FollowUpType,
  NamedResource,
} from "@/lib/api/contracts";
import { cn } from "@/lib/utils/class-names";

export type InboxTypeFilter = FollowUpType | "all";

const typeTabs: Array<{ value: InboxTypeFilter; label: string }> = [
  { value: "needs_call", label: "Needs call" },
  { value: "reschedule", label: "Reschedule" },
  { value: "declined", label: "Declined" },
  { value: "confirmed", label: "Confirmed" },
  { value: "all", label: "All" },
];

interface InboxFiltersProps {
  type: InboxTypeFilter;
  status: FollowUpStatus;
  assignedToMe: boolean;
  campaignId: string;
  search: string;
  summary?: FollowUpSummary;
  campaigns: NamedResource[];
  onTypeChange: (value: InboxTypeFilter) => void;
  onStatusChange: (value: FollowUpStatus) => void;
  onAssignedChange: (value: boolean) => void;
  onCampaignChange: (value: string) => void;
  onSearchChange: (value: string) => void;
}

/** Inbox primary tabs and secondary work-queue filters. */
export function InboxFilters(props: InboxFiltersProps): React.JSX.Element {
  return (
    <div className="space-y-4">
      <div
        className="border-border flex overflow-x-auto border-b"
        role="tablist"
      >
        {typeTabs.map((tab) => {
          const count =
            tab.value === "all"
              ? props.summary?.total
              : props.summary?.by_type[tab.value];
          return (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={props.type === tab.value}
              onClick={() => props.onTypeChange(tab.value)}
              className={cn(
                "focus-visible:outline-ring border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap focus-visible:outline-2",
                props.type === tab.value
                  ? "border-primary text-primary"
                  : "text-muted-foreground border-transparent",
              )}
            >
              {tab.label} {count === undefined ? "" : `(${count})`}
            </button>
          );
        })}
      </div>
      <div className="grid gap-3 md:grid-cols-[minmax(12rem,1fr)_auto_auto_minmax(14rem,1.5fr)]">
        <select
          aria-label="Follow-up status"
          value={props.status}
          onChange={(event) =>
            props.onStatusChange(event.target.value as FollowUpStatus)
          }
          className="border-border bg-surface rounded-control h-10 border px-3 text-sm"
        >
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
        </select>
        <select
          aria-label="Campaign"
          value={props.campaignId}
          onChange={(event) => props.onCampaignChange(event.target.value)}
          className="border-border bg-surface rounded-control h-10 border px-3 text-sm"
        >
          <option value="">All campaigns</option>
          {props.campaigns.map((campaign) => (
            <option key={campaign.id} value={campaign.id}>
              {campaign.name}
            </option>
          ))}
        </select>
        <label className="border-border bg-surface rounded-control flex h-10 items-center gap-2 border px-3 text-sm">
          <input
            type="checkbox"
            checked={props.assignedToMe}
            onChange={(event) => props.onAssignedChange(event.target.checked)}
          />
          Assigned to me
        </label>
        <Input
          aria-label="Search follow-ups"
          placeholder="Search donor or reply"
          value={props.search}
          onChange={(event) => props.onSearchChange(event.target.value)}
        />
      </div>
    </div>
  );
}
