import { AlertTriangle } from "lucide-react";

import type { DonorBatchDetail } from "@/hooks/use-donor-batches";
import type { ContentSeriesDetail } from "@/hooks/use-content-series";

import { CampaignScheduleTimeline } from "./campaign-schedule-timeline";

export function getLanguageCoverageWarnings(
  batch?: DonorBatchDetail,
  primary?: ContentSeriesDetail,
  secondary?: ContentSeriesDetail,
): string[] {
  if (!batch) return [];
  const donorLanguages = batch.language_breakdown
    .filter(({ count }) => count > 0)
    .map(({ language }) => language);
  const warnings: string[] = [];
  for (const [label, series] of [
    ["Primary series", primary],
    ["Secondary series", secondary],
  ] as const) {
    if (!series) continue;
    const missing = donorLanguages.filter(
      (language) => !series.languages.includes(language),
    );
    if (missing.length > 0) {
      warnings.push(
        `${label} is missing ${missing.map((code) => (code === "ur" ? "Urdu" : "English")).join(" and ")}.`,
      );
    }
  }
  return warnings;
}

/** Live campaign audience and sequence summary. */
export function CampaignSummary({
  batch,
  primary,
  secondary,
}: {
  batch?: DonorBatchDetail;
  primary?: ContentSeriesDetail;
  secondary?: ContentSeriesDetail;
}): React.JSX.Element {
  const warnings = getLanguageCoverageWarnings(batch, primary, secondary);
  return (
    <aside className="border-border bg-surface rounded-card space-y-6 border p-5">
      <div>
        <h2 className="text-lg font-semibold">Campaign summary</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Review the audience and complete schedule before launch.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <SummaryValue label="Valid donors" value={batch?.valid_rows ?? "—"} />
        <SummaryValue
          label="Languages"
          value={
            batch?.language_breakdown
              .map(
                ({ language, count }) => `${language.toUpperCase()} ${count}`,
              )
              .join(" · ") || "—"
          }
        />
      </div>
      {warnings.length > 0 ? (
        <div
          role="alert"
          className="border-warning/30 bg-warning/10 text-warning rounded-control border p-3 text-sm"
        >
          <p className="flex items-center gap-2 font-medium">
            <AlertTriangle aria-hidden="true" className="size-4" />
            Language coverage warning
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Schedule timeline</h3>
        <CampaignScheduleTimeline primary={primary} secondary={secondary} />
      </div>
    </aside>
  );
}

function SummaryValue({
  label,
  value,
}: {
  label: string;
  value: string | number;
}): React.JSX.Element {
  return (
    <div className="bg-surface-muted rounded-control p-3">
      <p className="text-muted-foreground text-xs">{label}</p>
      <p className="mt-1 font-semibold tabular-nums">{value}</p>
    </div>
  );
}
