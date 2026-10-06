import { Input } from "@/components/ui/input";
import type { NamedResource } from "@/lib/api/contracts";

interface MetricsFiltersProps {
  campaignId: string;
  from: string;
  to: string;
  campaigns: NamedResource[];
  onCampaignChange: (value: string) => void;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
}

/** Campaign and date scope shared by dashboard and report metrics. */
export function MetricsFilters(props: MetricsFiltersProps): React.JSX.Element {
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
