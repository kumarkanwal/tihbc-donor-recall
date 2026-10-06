import type { components, paths } from "@/lib/api/schema";

export type FollowUpType = components["schemas"]["FollowUpType"];
export type FollowUpStatus = components["schemas"]["FollowUpStatus"];
export type FollowUpPriority = components["schemas"]["FollowUpPriority"];
export type FollowUpOutcome = components["schemas"]["FollowUpResolveOutcome"];
export type FollowUpListItem = components["schemas"]["FollowUpListItem"];
export type FollowUpPage = components["schemas"]["FollowUpPage"];
export type FollowUpSummary = components["schemas"]["FollowUpInboxSummary"];
export type FollowUpDetail = components["schemas"]["FollowUpDetail"];
export type FollowUpFilters = NonNullable<
  paths["/api/v1/follow-ups"]["get"]["parameters"]["query"]
>;

export type MetricsFilters = NonNullable<
  paths["/api/v1/metrics/overview"]["get"]["parameters"]["query"]
>;
export type MetricsOverview = components["schemas"]["MetricsOverview"];
export type MetricsTimeseries = components["schemas"]["MetricsTimeseries"];
export type MetricsTimeseriesItem =
  components["schemas"]["MetricsTimeseriesItem"];
export type MetricsResponseBreakdown =
  components["schemas"]["MetricsResponseBreakdown"];
export type DeclineReasonMetrics =
  components["schemas"]["DeclineReasonMetrics"];
export type DeclineReasonMetric = components["schemas"]["DeclineReasonMetric"];
export type CampaignMetrics = components["schemas"]["CampaignMetrics"];
export type CampaignMetricRow = components["schemas"]["CampaignMetricRow"];
export type InactiveNumberPage = components["schemas"]["InactiveNumberPage"];
export type InactiveNumberRow = components["schemas"]["InactiveNumberRow"];
export type NamedResource = components["schemas"]["NamedResource"];

export type IntegrationSettings =
  components["schemas"]["IntegrationSettingsOut"];
export type DemoClock = components["schemas"]["DemoClockOut"];
export type DemoClockAdvance = components["schemas"]["DemoClockAdvance"];
