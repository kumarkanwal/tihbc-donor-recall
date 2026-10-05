import { apiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

/**
 * Temporary contracts for docs/api.md sections 8–10.
 * Remove each area as backend Tasks 2.10–2.12 add generated schema types.
 */

export type FollowUpType =
  "confirmed" | "reschedule" | "declined" | "needs_call";
export type FollowUpStatus = "open" | "in_progress" | "done";
export type FollowUpPriority = "normal" | "high";
export type FollowUpOutcome = "attended" | "rebooked" | "not_reachable";

export interface NamedPendingResource {
  id: string;
  name: string;
}

export interface PendingPage<Item> {
  items: Item[];
  total: number;
  page: number;
  page_size: number;
}

export interface FollowUpListItem {
  id: string;
  enrollment_id: string;
  donor: { id: string; name: string; phone: string };
  campaign: NamedPendingResource;
  type: FollowUpType;
  status: FollowUpStatus;
  priority: FollowUpPriority;
  latest_reply: { body: string; created_at: string } | null;
  assigned_to: { id: string; full_name: string } | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpSummary {
  total: number;
  by_type: Record<FollowUpType, number>;
  by_status: Record<FollowUpStatus, number>;
}

export interface FollowUpDetail extends FollowUpListItem {
  donor: {
    id: string;
    name: string;
    phone: string;
    language: "en" | "ur";
    segment: string;
    city: string | null;
    blood_group: string | null;
    last_donation_date: string | null;
  };
  enrollment: { id: string; status: string };
  latest_response: {
    intent: string;
    requested_date: string | null;
    decline_reason: string | null;
    confidence: number | null;
    raw_text: string;
    created_at: string;
  } | null;
  appointment: { center_name: string; slot_start: string } | null;
  activities: Array<{
    id: string;
    action: string;
    note: string | null;
    user_name: string | null;
    created_at: string;
  }>;
}

export interface FollowUpFilters {
  type?: FollowUpType;
  status?: FollowUpStatus;
  priority?: FollowUpPriority;
  campaign_id?: string;
  assigned_to?: "me";
  search?: string;
  page?: number;
  page_size?: number;
}

export interface MetricsFilters {
  campaign_id?: string;
  from?: string;
  to?: string;
}

export interface MetricsOverview {
  donors: number;
  sent: number;
  delivered: number;
  read: number;
  responded: number;
  delivery_rate: number;
  read_rate: number;
  response_rate: number;
  confirmed: number;
  rescheduled: number;
  declined: number;
  escalated: number;
  invalid_numbers: number;
  undeliverable: number;
}

export interface MetricsTimeseriesItem {
  date: string;
  sent: number;
  delivered: number;
  read: number;
  responded: number;
}

export interface MetricsResponseBreakdown {
  by_intent: Record<string, number>;
  by_segment: Record<string, number>;
  by_language: Record<string, number>;
}

export interface DeclineReasonMetric {
  decline_reason: string;
  count: number;
}

export interface CampaignMetricRow {
  campaign_id: string;
  campaign_name: string;
  batch_name: string;
  status: string;
  enrolled: number;
  sent: number;
  delivered: number;
  read: number;
  responded: number;
  response_rate: number;
}

export interface InactiveNumberRow {
  id: string;
  donor_name: string;
  phone: string;
  kind: "invalid" | "undeliverable";
  reason: string;
  batch_name: string;
  campaign_name: string | null;
  occurred_at: string;
}

export interface InactiveNumberSummary {
  invalid: number;
  undeliverable: number;
  total: number;
}

export interface InactiveNumberPage extends PendingPage<InactiveNumberRow> {
  summary: InactiveNumberSummary;
}

export interface IntegrationTemplate {
  name: string;
  status: string;
  category: string;
}

export interface IntegrationSettings {
  business_verified: boolean;
  phone_number: string;
  display_name: string;
  quality_rating: string;
  messaging_limit: string | number;
  templates: IntegrationTemplate[];
}

type PendingResult<Data> = Promise<{
  data?: Data;
  error?: unknown;
  response: Response;
}>;

export interface PendingApiClient {
  GET(path: "/api/v1/settings/integration"): PendingResult<IntegrationSettings>;
  GET(
    path: "/api/v1/follow-ups",
    options: { params: { query: FollowUpFilters } },
  ): PendingResult<PendingPage<FollowUpListItem>>;
  GET(
    path: "/api/v1/follow-ups/summary",
    options: { params: { query: FollowUpFilters } },
  ): PendingResult<FollowUpSummary>;
  GET(
    path: "/api/v1/follow-ups/{id}",
    options: { params: { path: { id: string } } },
  ): PendingResult<FollowUpDetail>;
  GET(
    path: "/api/v1/follow-ups/export",
    options: { params: { query: FollowUpFilters }; parseAs: "blob" },
  ): PendingResult<Blob>;
  PATCH(
    path: "/api/v1/follow-ups/{id}",
    options: {
      params: { path: { id: string } };
      body: {
        status?: FollowUpStatus;
        assigned_to_id?: string;
        priority?: FollowUpPriority;
      };
    },
  ): PendingResult<FollowUpDetail>;
  POST(
    path: "/api/v1/follow-ups/{id}/notes",
    options: { params: { path: { id: string } }; body: { note: string } },
  ): PendingResult<FollowUpDetail>;
  POST(
    path: "/api/v1/follow-ups/{id}/actions/resolve",
    options: {
      params: { path: { id: string } };
      body: { outcome: FollowUpOutcome; note?: string };
    },
  ): PendingResult<FollowUpDetail>;
  POST(path: "/api/v1/demo/actions/reset-data"): PendingResult<unknown>;
  GET(
    path: "/api/v1/metrics/overview",
    options: { params: { query: MetricsFilters } },
  ): PendingResult<MetricsOverview>;
  GET(
    path: "/api/v1/metrics/timeseries",
    options: { params: { query: MetricsFilters } },
  ): PendingResult<{ items: MetricsTimeseriesItem[] }>;
  GET(
    path: "/api/v1/metrics/response-breakdown",
    options: { params: { query: MetricsFilters } },
  ): PendingResult<MetricsResponseBreakdown>;
  GET(
    path: "/api/v1/metrics/decline-reasons",
    options: { params: { query: MetricsFilters } },
  ): PendingResult<{ items: DeclineReasonMetric[] }>;
  GET(
    path: "/api/v1/metrics/campaigns",
    options: { params: { query: MetricsFilters } },
  ): PendingResult<{ items: CampaignMetricRow[] }>;
  GET(
    path: "/api/v1/reports/inactive-numbers",
    options: {
      params: { query: MetricsFilters & { page?: number; page_size?: number } };
    },
  ): PendingResult<InactiveNumberPage>;
  GET(
    path: "/api/v1/reports/{report}/export",
    options: {
      params: {
        path: {
          report: "inactive-numbers" | "response-breakdown" | "campaigns";
        };
        query: MetricsFilters;
      };
      parseAs: "blob";
    },
  ): PendingResult<Blob>;
}

export const pendingApiClient = apiClient as unknown as PendingApiClient;

/** Identify endpoints intentionally waiting for backend Tasks 2.10/2.11. */
export function isPendingBackendUpdate(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}
