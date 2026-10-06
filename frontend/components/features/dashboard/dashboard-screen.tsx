"use client";

import { useMemo, useState } from "react";

import { ErrorState } from "@/components/shared/error-state";
import { MetricsFilters } from "@/components/shared/metrics-filters";
import { PageHeader } from "@/components/shared/page-header";
import { useCampaignCatalog } from "@/hooks/use-campaigns";
import { useFollowUps } from "@/hooks/use-follow-ups";
import {
  useCampaignMetrics,
  useDeclineReasons,
  useMetricsOverview,
  useMetricsResponseBreakdown,
  useMetricsTimeseries,
} from "@/hooks/use-metrics";
import type { MetricsFilters as MetricsFilterValues } from "@/lib/api/contracts";

import { ActiveCampaignsTable } from "./active-campaigns-table";
import { DailyActivityChart } from "./daily-activity-chart";
import { DashboardInsight } from "./dashboard-insight";
import { DashboardKpis } from "./dashboard-kpis";
import { RecentFollowUps } from "./recent-follow-ups";
import { ResponseOutcomeChart } from "./response-outcome-chart";

/** Aggregate campaign health and current coordinator workload. */
export function DashboardScreen(): React.JSX.Element {
  const [campaignId, setCampaignId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const filters = useMemo<MetricsFilterValues>(
    () => ({
      campaign_id: campaignId || undefined,
      from: from || undefined,
      to: to || undefined,
    }),
    [campaignId, from, to],
  );
  const overview = useMetricsOverview(filters);
  const timeseries = useMetricsTimeseries(filters);
  const breakdown = useMetricsResponseBreakdown(filters);
  const declineReasons = useDeclineReasons(filters);
  const campaignMetrics = useCampaignMetrics(filters);
  const followUps = useFollowUps({
    status: "open",
    campaign_id: filters.campaign_id,
    page: 1,
    page_size: 5,
  });
  const campaigns = useCampaignCatalog(undefined);
  const queries = [
    overview,
    timeseries,
    breakdown,
    declineReasons,
    campaignMetrics,
    followUps,
  ];

  function retryAll(): void {
    for (const query of queries) void query.refetch();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Monitor donor recall activity and campaign performance."
      />
      <MetricsFilters
        campaignId={campaignId}
        from={from}
        to={to}
        campaigns={
          campaigns.data?.items.map(({ id, name }) => ({ id, name })) ?? []
        }
        onCampaignChange={setCampaignId}
        onFromChange={setFrom}
        onToChange={setTo}
      />
      {overview.error ? (
        <ErrorState
          description="Dashboard metrics could not be loaded."
          onRetry={retryAll}
        />
      ) : (
        <>
          {overview.data ? (
            <DashboardKpis metrics={overview.data} />
          ) : (
            <div
              aria-label="Loading campaign performance summary"
              className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
            >
              {Array.from({ length: 6 }, (_, index) => (
                <div
                  key={index}
                  className="bg-surface-muted rounded-card h-32 animate-pulse"
                />
              ))}
            </div>
          )}
          <div className="grid gap-6 xl:grid-cols-2">
            <DailyActivityChart
              items={timeseries.data?.items}
              isLoading={timeseries.isPending}
              error={
                timeseries.error
                  ? "Daily activity could not be loaded."
                  : undefined
              }
              onRetry={() => void timeseries.refetch()}
            />
            <ResponseOutcomeChart
              metrics={overview.data}
              isLoading={overview.isPending}
              error={
                overview.error
                  ? "Response outcomes could not be loaded."
                  : undefined
              }
              onRetry={() => void overview.refetch()}
            />
          </div>
          <ActiveCampaignsTable items={campaignMetrics.data?.items} />
          <div className="grid gap-6 xl:grid-cols-2">
            <RecentFollowUps items={followUps.data?.items} />
            <DashboardInsight
              breakdown={breakdown.data}
              declineReasons={declineReasons.data?.items}
            />
          </div>
        </>
      )}
    </div>
  );
}
