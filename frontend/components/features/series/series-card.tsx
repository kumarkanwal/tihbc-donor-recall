import { SeriesActions } from "@/components/features/series/series-actions";
import { StatusBadge } from "@/components/shared/status-badge";
import type { ContentSeries } from "@/hooks/use-content-series";

/** Grid representation of a content-series summary. */
export function SeriesCard({
  series,
}: {
  series: ContentSeries;
}): React.JSX.Element {
  return (
    <article className="border-border bg-surface rounded-card flex min-h-64 flex-col border p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">{series.name}</h2>
          <p className="text-muted-foreground mt-1 line-clamp-2 text-sm">
            {series.description || "No description"}
          </p>
        </div>
        <StatusBadge
          status={series.kind}
          label={series.kind === "primary" ? "Primary" : "Secondary"}
        />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge status={series.status} />
        {series.languages.map((language) => (
          <span
            key={language}
            className="bg-primary-soft text-primary rounded-control px-2.5 py-1 text-xs font-medium"
          >
            {language === "en" ? "English" : "Urdu"}
          </span>
        ))}
      </div>
      <p className="text-muted-foreground mt-4 text-sm tabular-nums">
        {series.step_count} {series.step_count === 1 ? "step" : "steps"}
      </p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {series.tags.length ? (
          series.tags.map((tag) => (
            <span
              key={tag}
              className="border-border rounded-control border px-2 py-1 text-xs"
            >
              {tag}
            </span>
          ))
        ) : (
          <span className="text-muted-foreground text-xs">No tags</span>
        )}
      </div>
      <div className="mt-auto pt-5">
        <SeriesActions series={series} compact />
      </div>
    </article>
  );
}
