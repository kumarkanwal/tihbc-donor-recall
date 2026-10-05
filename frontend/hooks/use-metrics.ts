"use client";

import {
  useMutation,
  useQuery,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  pendingApiClient,
  type CampaignMetricRow,
  type DeclineReasonMetric,
  type MetricsFilters,
  type MetricsOverview,
  type MetricsResponseBreakdown,
  type MetricsTimeseriesItem,
  type InactiveNumberPage,
} from "@/lib/api/pending-contracts";
import { requireResponseData } from "@/lib/api/response";
import { downloadBlob } from "@/lib/utils/download";

export const metricsKeys = {
  all: ["metrics"] as const,
  overview: (filters: MetricsFilters) =>
    [...metricsKeys.all, "overview", filters] as const,
  timeseries: (filters: MetricsFilters) =>
    [...metricsKeys.all, "timeseries", filters] as const,
  responseBreakdown: (filters: MetricsFilters) =>
    [...metricsKeys.all, "response-breakdown", filters] as const,
  declineReasons: (filters: MetricsFilters) =>
    [...metricsKeys.all, "decline-reasons", filters] as const,
  campaigns: (filters: MetricsFilters) =>
    [...metricsKeys.all, "campaigns", filters] as const,
  inactiveNumbers: (
    filters: MetricsFilters & { page: number; page_size: number },
  ) => [...metricsKeys.all, "inactive-numbers", filters] as const,
};

export function useMetricsOverview(
  filters: MetricsFilters,
): UseQueryResult<MetricsOverview> {
  return useQuery({
    queryKey: metricsKeys.overview(filters),
    queryFn: async () => {
      const { data } = await pendingApiClient.GET("/api/v1/metrics/overview", {
        params: { query: filters },
      });
      return requireResponseData(data, "Metrics overview");
    },
  });
}

export function useMetricsTimeseries(
  filters: MetricsFilters,
): UseQueryResult<{ items: MetricsTimeseriesItem[] }> {
  return useQuery({
    queryKey: metricsKeys.timeseries(filters),
    queryFn: async () => {
      const { data } = await pendingApiClient.GET(
        "/api/v1/metrics/timeseries",
        {
          params: { query: filters },
        },
      );
      return requireResponseData(data, "Metrics timeseries");
    },
  });
}

export function useMetricsResponseBreakdown(
  filters: MetricsFilters,
): UseQueryResult<MetricsResponseBreakdown> {
  return useQuery({
    queryKey: metricsKeys.responseBreakdown(filters),
    queryFn: async () => {
      const { data } = await pendingApiClient.GET(
        "/api/v1/metrics/response-breakdown",
        { params: { query: filters } },
      );
      return requireResponseData(data, "Response breakdown");
    },
  });
}

export function useDeclineReasons(
  filters: MetricsFilters,
): UseQueryResult<{ items: DeclineReasonMetric[] }> {
  return useQuery({
    queryKey: metricsKeys.declineReasons(filters),
    queryFn: async () => {
      const { data } = await pendingApiClient.GET(
        "/api/v1/metrics/decline-reasons",
        { params: { query: filters } },
      );
      return requireResponseData(data, "Decline reasons");
    },
  });
}

export function useCampaignMetrics(
  filters: MetricsFilters,
): UseQueryResult<{ items: CampaignMetricRow[] }> {
  return useQuery({
    queryKey: metricsKeys.campaigns(filters),
    queryFn: async () => {
      const { data } = await pendingApiClient.GET("/api/v1/metrics/campaigns", {
        params: { query: filters },
      });
      return requireResponseData(data, "Campaign metrics");
    },
  });
}

export function useInactiveNumbers(
  filters: MetricsFilters & { page: number; page_size: number },
): UseQueryResult<InactiveNumberPage> {
  return useQuery({
    queryKey: metricsKeys.inactiveNumbers(filters),
    queryFn: async () => {
      const { data } = await pendingApiClient.GET(
        "/api/v1/reports/inactive-numbers",
        { params: { query: filters } },
      );
      return requireResponseData(data, "Inactive number report");
    },
  });
}

export type ReportExport =
  "inactive-numbers" | "response-breakdown" | "campaigns";

export function useExportReport(report: ReportExport, filters: MetricsFilters) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await pendingApiClient.GET(
        "/api/v1/reports/{report}/export",
        {
          params: { path: { report }, query: filters },
          parseAs: "blob",
        },
      );
      return requireResponseData(data, "Report export");
    },
    onSuccess: (blob) => downloadBlob(blob, `tihbc-${report}.csv`),
  });
}
