import { z } from "zod";

import type { CampaignCreate, CampaignDetail } from "@/hooks/use-campaigns";

export const campaignFormSchema = z
  .object({
    name: z.string().trim().min(1, "Enter a campaign name.").max(120),
    batch_id: z.string().min(1, "Select a donor batch."),
    primary_series_id: z.string().min(1, "Select a primary series."),
    secondary_series_id: z.string().min(1, "Select a secondary series."),
    start_mode: z.enum(["now", "scheduled"]),
    start_local: z.string(),
  })
  .superRefine((value, context) => {
    if (value.start_mode === "scheduled" && !value.start_local) {
      context.addIssue({
        code: "custom",
        path: ["start_local"],
        message: "Choose a campaign start date and time.",
      });
    }
  });

export type CampaignFormValues = z.infer<typeof campaignFormSchema>;

function toKarachiLocal(value: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(value));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((item) => item.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
}

export function getCampaignFormDefaults(
  campaign?: CampaignDetail,
): CampaignFormValues {
  const isFuture = campaign
    ? new Date(campaign.start_at).getTime() > Date.now() + 60_000
    : false;
  return {
    name: campaign?.name ?? "",
    batch_id: campaign?.batch.id ?? "",
    primary_series_id: campaign?.primary_series.id ?? "",
    secondary_series_id: campaign?.secondary_series.id ?? "",
    start_mode: isFuture ? "scheduled" : "now",
    start_local: campaign ? toKarachiLocal(campaign.start_at) : "",
  };
}

/** Convert a Karachi-local form value to the API's UTC timestamp. */
export function toCampaignInput(values: CampaignFormValues): CampaignCreate {
  const startAt =
    values.start_mode === "now"
      ? new Date().toISOString()
      : new Date(`${values.start_local}:00+05:00`).toISOString();
  return {
    name: values.name.trim(),
    batch_id: values.batch_id,
    primary_series_id: values.primary_series_id,
    secondary_series_id: values.secondary_series_id,
    start_at: startAt,
  };
}
