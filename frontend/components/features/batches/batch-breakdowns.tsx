import type { BatchPreview, DonorBatchDetail } from "@/hooks/use-donor-batches";

type BreakdownSource = Pick<
  BatchPreview | DonorBatchDetail,
  "segment_breakdown" | "language_breakdown"
>;

const languageLabels = { en: "English", ur: "Urdu" } as const;

/** Show segment and language counts from a preview or imported batch. */
export function BatchBreakdowns({
  segment_breakdown,
  language_breakdown,
}: BreakdownSource): React.JSX.Element {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <BreakdownCard
        title="Segments"
        rows={segment_breakdown.map(({ segment, count }) => ({
          label: segment.replaceAll("_", " "),
          count,
        }))}
      />
      <BreakdownCard
        title="Languages"
        rows={language_breakdown.map(({ language, count }) => ({
          label: languageLabels[language],
          count,
        }))}
      />
    </div>
  );
}

function BreakdownCard({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; count: number }[];
}): React.JSX.Element {
  return (
    <section className="border-border bg-surface rounded-card border p-5">
      <h3 className="font-semibold">{title}</h3>
      <dl className="mt-3 space-y-2">
        {rows.map(({ label, count }) => (
          <div
            key={label}
            className="flex items-center justify-between gap-4 text-sm"
          >
            <dt className="capitalize">{label}</dt>
            <dd className="font-medium tabular-nums">{count}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
