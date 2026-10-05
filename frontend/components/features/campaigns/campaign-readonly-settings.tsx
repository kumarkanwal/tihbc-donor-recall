import { DateTime } from "@/components/shared/date-time";
import type { CampaignDetail } from "@/hooks/use-campaigns";

/** Immutable campaign assignment summary for non-draft campaigns. */
export function CampaignReadonlySettings({
  campaign,
}: {
  campaign: CampaignDetail;
}): React.JSX.Element {
  const items = [
    ["Donor batch", campaign.batch.name],
    ["Primary series", campaign.primary_series.name],
    ["Secondary series", campaign.secondary_series.name],
  ] as const;
  return (
    <section className="border-border bg-surface rounded-card border p-5">
      <h2 className="text-lg font-semibold">Campaign settings</h2>
      <p className="text-muted-foreground mt-1 text-sm">
        Campaign assignments are read-only after launch.
      </p>
      <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map(([label, value]) => (
          <div key={label}>
            <dt className="text-muted-foreground text-xs">{label}</dt>
            <dd className="mt-1 text-sm font-medium">{value}</dd>
          </div>
        ))}
        <div>
          <dt className="text-muted-foreground text-xs">Start</dt>
          <dd className="mt-1 text-sm font-medium">
            <DateTime value={campaign.start_at} />
          </dd>
        </div>
      </dl>
    </section>
  );
}
