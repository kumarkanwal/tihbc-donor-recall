import { useContentSeriesDetail } from "@/hooks/use-content-series";

import { CampaignScheduleTimeline } from "./campaign-schedule-timeline";

/** Read-only sequence timeline; per-step metrics intentionally await metrics APIs. */
export function CampaignSequenceTimeline({
  primarySeriesId,
  secondarySeriesId,
}: {
  primarySeriesId: string;
  secondarySeriesId: string;
}): React.JSX.Element {
  const primary = useContentSeriesDetail(primarySeriesId);
  const secondary = useContentSeriesDetail(secondarySeriesId);
  return (
    <section className="border-border bg-surface rounded-card border p-5">
      <h2 className="text-lg font-semibold">Sequence timeline</h2>
      <p className="text-muted-foreground mt-1 mb-5 text-sm">
        Per-step sent, delivered, read, and response metrics will appear when
        campaign metrics are available.
      </p>
      {primary.isPending || secondary.isPending ? (
        <div aria-label="Loading sequence" className="space-y-3">
          {[0, 1, 2].map((item) => (
            <div
              key={item}
              className="bg-surface-muted h-10 animate-pulse rounded"
            />
          ))}
        </div>
      ) : primary.error || secondary.error ? (
        <p role="alert" className="text-danger text-sm">
          The sequence timeline could not be loaded.
        </p>
      ) : (
        <CampaignScheduleTimeline
          primary={primary.data}
          secondary={secondary.data}
        />
      )}
    </section>
  );
}
