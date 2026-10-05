import { Input } from "@/components/ui/input";
import type { NamedPendingResource } from "@/lib/api/pending-contracts";

interface DashboardFiltersProps {
  campaignId: string;
  from: string;
  to: string;
  campaigns: NamedPendingResource[];
  onCampaignChange: (value: string) => void;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
}

/** Shared dashboard scope filters defined by the metrics contract. */
export function DashboardFilters(
  props: DashboardFiltersProps,
): React.JSX.Element {
  return (
    <section className="rounded-card border-border bg-surface shadow-surface grid gap-4 border p-4 md:grid-cols-3">
      <label className="space-y-1.5 text-sm font-medium">
        <span>Campaign</span>
        <select
          value={props.campaignId}
          onChange={(event) => props.onCampaignChange(event.target.value)}
          className="border-border bg-surface rounded-control h-10 w-full border px-3 font-normal"
        >
          <option value="">All campaigns</option>
          {props.campaigns.map((campaign) => (
            <option key={campaign.id} value={campaign.id}>
              {campaign.name}
            </option>
          ))}
        </select>
      </label>
      <label className="space-y-1.5 text-sm font-medium">
        <span>From</span>
        <Input
          type="date"
          value={props.from}
          onChange={(event) => props.onFromChange(event.target.value)}
        />
      </label>
      <label className="space-y-1.5 text-sm font-medium">
        <span>To</span>
        <Input
          type="date"
          value={props.to}
          min={props.from || undefined}
          onChange={(event) => props.onToChange(event.target.value)}
        />
      </label>
    </section>
  );
}
