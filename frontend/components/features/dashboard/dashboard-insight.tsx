import type {
  DeclineReasonMetric,
  MetricsResponseBreakdown,
} from "@/lib/api/pending-contracts";

interface DashboardInsightProps {
  breakdown?: MetricsResponseBreakdown;
  declineReasons?: DeclineReasonMetric[];
}

function topEntry(values: Record<string, number>): [string, number] | null {
  return (
    Object.entries(values).sort((left, right) => right[1] - left[1])[0] ?? null
  );
}

/** Deterministic, plain-language observations from current aggregate data. */
export function DashboardInsight({
  breakdown,
  declineReasons = [],
}: DashboardInsightProps): React.JSX.Element {
  const segment = breakdown ? topEntry(breakdown.by_segment) : null;
  const language = breakdown ? topEntry(breakdown.by_language) : null;
  const decline = [...declineReasons].sort(
    (left, right) => right.count - left.count,
  )[0];

  return (
    <section className="rounded-card border-border bg-surface shadow-surface border p-5">
      <h2 className="text-lg font-semibold">What the data shows</h2>
      <div className="text-muted-foreground mt-3 space-y-2 text-sm">
        {segment ? (
          <p>
            The {segment[0].replaceAll("_", " ")} segment has the most recorded
            responses ({segment[1]}).
          </p>
        ) : null}
        {language ? (
          <p>
            {language[0] === "ur" ? "Urdu" : "English"} accounts for the largest
            response group ({language[1]}).
          </p>
        ) : null}
        {decline ? (
          <p>
            The most common decline reason is{" "}
            {decline.decline_reason.replaceAll("_", " ")} ({decline.count}).
          </p>
        ) : null}
        {!segment && !language && !decline ? (
          <p>Insights will appear when response activity is available.</p>
        ) : null}
      </div>
    </section>
  );
}
