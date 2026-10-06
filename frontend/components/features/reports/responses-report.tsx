import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import {
  useDeclineReasons,
  useMetricsResponseBreakdown,
} from "@/hooks/use-metrics";
import { type MetricsFilters } from "@/lib/api/contracts";

import { BreakdownChart } from "./breakdown-chart";

interface ResponsesReportProps {
  filters: MetricsFilters;
}

function displayLabel(value: string): string {
  if (value === "en") return "English";
  if (value === "ur") return "Urdu";
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

/** Response distributions across intent, donor segment, and language. */
export function ResponsesReport({
  filters,
}: ResponsesReportProps): React.JSX.Element {
  const breakdown = useMetricsResponseBreakdown(filters);
  const declineReasons = useDeclineReasons(filters);
  if (breakdown.error || declineReasons.error) {
    return (
      <ErrorState
        description="The response report could not be loaded."
        onRetry={() => {
          void breakdown.refetch();
          void declineReasons.refetch();
        }}
      />
    );
  }
  if (!breakdown.data || declineReasons.isPending) {
    return <div className="bg-surface-muted rounded-card h-72 animate-pulse" />;
  }

  const declineValues = Object.fromEntries(
    (declineReasons.data?.items ?? []).map((item) => [
      item.decline_reason,
      item.count,
    ]),
  );
  const rows = [
    ...Object.entries(breakdown.data.by_intent).map(([label, count]) => ({
      dimension: "Intent",
      label,
      count,
    })),
    ...Object.entries(breakdown.data.by_segment).map(([label, count]) => ({
      dimension: "Segment",
      label,
      count,
    })),
    ...Object.entries(breakdown.data.by_language).map(([label, count]) => ({
      dimension: "Language",
      label,
      count,
    })),
  ];

  return (
    <div className="space-y-6" role="tabpanel">
      <div className="grid gap-6 xl:grid-cols-2">
        <BreakdownChart
          title="Responses by intent"
          description="Classified donor response outcomes"
          values={breakdown.data.by_intent}
        />
        <BreakdownChart
          title="Responses by segment"
          description="Response volume by donor segment"
          values={breakdown.data.by_segment}
        />
        <BreakdownChart
          title="Responses by language"
          description="English and Urdu response volume"
          values={breakdown.data.by_language}
        />
        <BreakdownChart
          title="Decline reasons"
          description="Recorded reasons from declined donors"
          values={declineValues}
        />
      </div>
      <section className="rounded-card border-border bg-surface shadow-surface overflow-hidden border">
        <header className="px-5 py-4">
          <h2 className="text-lg font-semibold">Response breakdown</h2>
          <p className="text-muted-foreground text-sm">
            Counts behind the intent, segment, and language charts
          </p>
        </header>
        {rows.length ? (
          <table className="w-full text-left text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className="px-5 py-3 font-medium">Dimension</th>
                <th className="px-5 py-3 font-medium">Group</th>
                <th className="px-5 py-3 text-right font-medium">Responses</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`${row.dimension}-${row.label}`}
                  className="border-border border-t"
                >
                  <td className="px-5 py-3">{row.dimension}</td>
                  <td className="px-5 py-3">{displayLabel(row.label)}</td>
                  <td className="px-5 py-3 text-right tabular-nums">
                    {row.count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState
            title="No responses yet"
            description="Response breakdowns will appear after donors reply."
            className="min-h-56 rounded-none border-0 border-t"
          />
        )}
      </section>
    </div>
  );
}
