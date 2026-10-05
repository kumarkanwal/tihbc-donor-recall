import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { useCampaignMetrics, useMetricsOverview } from "@/hooks/use-metrics";
import {
  isPendingBackendUpdate,
  type MetricsFilters,
} from "@/lib/api/pending-contracts";

interface DeliveryReportProps {
  filters: MetricsFilters;
}

/** Sent-to-response funnel and campaign comparison table. */
export function DeliveryReport({
  filters,
}: DeliveryReportProps): React.JSX.Element {
  const overview = useMetricsOverview(filters);
  const campaigns = useCampaignMetrics(filters);
  const unavailable = [overview.error, campaigns.error].some(
    isPendingBackendUpdate,
  );

  if (unavailable) {
    return (
      <EmptyState
        title="Available after backend update"
        description="Delivery reports will be connected after backend Task 2.11."
      />
    );
  }
  if (overview.error || campaigns.error) {
    return (
      <ErrorState
        description="The delivery and engagement report could not be loaded."
        onRetry={() => {
          void overview.refetch();
          void campaigns.refetch();
        }}
      />
    );
  }
  if (!overview.data || campaigns.isPending) {
    return <div className="bg-surface-muted rounded-card h-72 animate-pulse" />;
  }

  const funnel = [
    ["Sent", overview.data.sent],
    ["Delivered", overview.data.delivered],
    ["Read", overview.data.read],
    ["Responded", overview.data.responded],
  ] as const;

  return (
    <div className="space-y-6" role="tabpanel">
      <section className="grid items-center gap-3 sm:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr]">
        {funnel.map(([label, value], index) => (
          <div key={label} className="contents">
            <article className="rounded-card border-border bg-surface shadow-surface border p-5 text-center">
              <p className="text-muted-foreground text-sm">{label}</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums">
                {value.toLocaleString()}
              </p>
            </article>
            {index < funnel.length - 1 ? (
              <ArrowRight
                aria-hidden="true"
                className="text-muted-foreground mx-auto hidden size-5 sm:block"
              />
            ) : null}
          </div>
        ))}
      </section>
      <section className="rounded-card border-border bg-surface shadow-surface overflow-hidden border">
        <header className="px-5 py-4">
          <h2 className="text-lg font-semibold">Campaign comparison</h2>
          <p className="text-muted-foreground text-sm">
            Delivery, reading, and response totals by campaign
          </p>
        </header>
        {campaigns.data?.items.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[48rem] text-left text-sm">
              <thead className="bg-surface-muted">
                <tr>
                  {[
                    "Campaign",
                    "Status",
                    "Sent",
                    "Delivered",
                    "Read",
                    "Responded",
                    "Response rate",
                  ].map((heading) => (
                    <th key={heading} className="px-4 py-3 font-medium">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {campaigns.data.items.map((campaign) => (
                  <tr
                    key={campaign.campaign_id}
                    className="border-border border-t"
                  >
                    <td className="px-4 py-3 font-medium">
                      <Link href={`/campaigns/${campaign.campaign_id}`}>
                        {campaign.campaign_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={campaign.status} />
                    </td>
                    <td className="px-4 py-3 tabular-nums">{campaign.sent}</td>
                    <td className="px-4 py-3 tabular-nums">
                      {campaign.delivered}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{campaign.read}</td>
                    <td className="px-4 py-3 tabular-nums">
                      {campaign.responded}
                    </td>
                    <td className="px-4 py-3 tabular-nums">
                      {campaign.response_rate.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="No campaign activity"
            description="Campaign metrics will appear when messages are sent."
            className="min-h-56 rounded-none border-0 border-t"
          />
        )}
      </section>
    </div>
  );
}
