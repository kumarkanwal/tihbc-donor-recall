import type { components } from "@/lib/api/schema";
import type { SimulatorMessage } from "@/lib/simulator/types";

type MessageStatus = components["schemas"]["MessageStatus"];
type EnrollmentStatus = components["schemas"]["EnrollmentStatus"];
type CampaignStatus = components["schemas"]["CampaignStatus"];
type FollowUpType = components["schemas"]["FollowUpType"];
type FollowUpStatus = components["schemas"]["FollowUpStatus"];
type FollowUpPriority = components["schemas"]["FollowUpPriority"];

export interface FollowUpListItem {
  id: string;
  enrollment_id: string;
  type: FollowUpType;
  status: FollowUpStatus;
  priority: FollowUpPriority;
  assigned_to_id: string | null;
  created_at: string;
  updated_at: string;
}

interface RealtimePayloads {
  "message.created": SimulatorMessage;
  "message.status_updated": {
    id: string;
    donor_id: string;
    status: MessageStatus;
    delivered_at: string | null;
    read_at: string | null;
    failed_reason: string | null;
  };
  "simulator.typing": { donor_id: string; is_typing: boolean };
  "enrollment.updated": {
    id: string;
    campaign_id: string;
    donor_id: string;
    status: EnrollmentStatus;
    current_series_kind: "primary" | "secondary" | null;
    current_step_order: number | null;
  };
  "followup.created": FollowUpListItem;
  "followup.updated": FollowUpListItem;
  "campaign.updated": {
    id: string;
    status: CampaignStatus;
    counts: Record<string, number>;
  };
  "metrics.updated": { campaign_id: string | null };
  "clock.updated": { now: string; offset_seconds: number };
}

export type RealtimeEventType = keyof RealtimePayloads;
export type RealtimeEvent = {
  [Type in RealtimeEventType]: {
    type: Type;
    payload: RealtimePayloads[Type];
    ts: string;
  };
}[RealtimeEventType];

const eventTypes = new Set<RealtimeEventType>([
  "message.created",
  "message.status_updated",
  "simulator.typing",
  "enrollment.updated",
  "followup.created",
  "followup.updated",
  "campaign.updated",
  "metrics.updated",
  "clock.updated",
]);

/** Parse known server envelopes; unknown and malformed events are ignored. */
export function parseRealtimeEvent(value: unknown): RealtimeEvent | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  if (
    typeof candidate.type !== "string" ||
    !eventTypes.has(candidate.type as RealtimeEventType) ||
    !candidate.payload ||
    typeof candidate.payload !== "object" ||
    typeof candidate.ts !== "string"
  ) {
    return null;
  }
  return candidate as unknown as RealtimeEvent;
}
