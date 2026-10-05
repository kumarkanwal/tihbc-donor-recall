import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import type { CampaignMetricRow } from "@/lib/api/pending-contracts";

interface ActiveCampaignsTableProps {
  items?: CampaignMetricRow[];
}

/** Compact campaign performance table for the dashboard. */
export function ActiveCampaignsTable({
  items = [],
}: ActiveCampaignsTableProps): React.JSX.Element {
  const active = items.filter((item) =>
    ["running", "scheduled", "paused"].includes(item.status),
  );

  return (
    <section className="rounded-card border-border bg-surface shadow-surface overflow-hidden border">
      <header className="flex items-center justify-between gap-4 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold">Active campaigns</h2>
          <p className="text-muted-foreground text-sm">
            Current enrollment and response progress
          </p>
        </div>
        <Link className="text-primary text-sm font-medium" href="/campaigns">
          View all
        </Link>
      </header>
      {active.length === 0 ? (
        <EmptyState
          title="No active campaigns"
          description="Running and scheduled campaigns will appear here."
          className="min-h-48 rounded-none border-0 border-t"
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[42rem] text-left text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className="px-5 py-3 font-medium">Campaign</th>
                <th className="px-5 py-3 font-medium">Batch</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Progress</th>
                <th className="px-5 py-3 font-medium">Response rate</th>
              </tr>
            </thead>
            <tbody>
              {active.map((campaign) => {
                const progress = campaign.enrolled
                  ? (campaign.responded / campaign.enrolled) * 100
                  : 0;
                return (
                  <tr
                    key={campaign.campaign_id}
                    className="border-border border-t"
                  >
                    <td className="px-5 py-3 font-medium">
                      <Link
                        className="hover:text-primary"
                        href={`/campaigns/${campaign.campaign_id}`}
                      >
                        {campaign.campaign_name}
                      </Link>
                    </td>
                    <td className="px-5 py-3">{campaign.batch_name}</td>
                    <td className="px-5 py-3">
                      <StatusBadge status={campaign.status} />
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <div className="bg-surface-muted h-2 w-24 overflow-hidden rounded-full">
                          <div
                            className="bg-primary h-full rounded-full"
                            style={{ width: `${Math.min(progress, 100)}%` }}
                          />
                        </div>
                        <span className="tabular-nums">
                          {campaign.responded}/{campaign.enrolled}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3 tabular-nums">
                      {campaign.response_rate.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
