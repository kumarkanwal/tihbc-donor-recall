import { z } from "zod";

import type {
  SeriesLanguage,
  SeriesStep,
  SeriesStepInput,
} from "@/hooks/use-content-series";

export const stepFormSchema = z.object({
  delay_days: z.number().int().min(0, "Delay cannot be negative.").max(365),
  category: z.enum(["utility", "marketing"]),
  media_type: z.enum(["none", "image", "video"]),
  media_url: z.string().nullable(),
  contents: z.object({
    en: z.string().max(1024, "Use 1024 characters or fewer."),
    ur: z.string().max(1024, "Use 1024 characters or fewer."),
  }),
  buttons: z
    .array(
      z.object({
        intent: z.enum(["confirm", "reschedule", "decline"]),
        labels: z.object({
          en: z.string().max(20, "Use 20 characters or fewer."),
          ur: z.string().max(20, "Use 20 characters or fewer."),
        }),
      }),
    )
    .max(3, "A step can have up to 3 buttons."),
});

export type SeriesStepFormValues = z.infer<typeof stepFormSchema>;

export function getStepDefaults(step?: SeriesStep): SeriesStepFormValues {
  const body = (language: SeriesLanguage) =>
    step?.contents.find((content) => content.language === language)?.body ?? "";
  return {
    delay_days: step?.delay_days ?? 0,
    category: step?.category ?? "utility",
    media_type: step?.media_type ?? "none",
    media_url: step?.media_url ?? null,
    contents: { en: body("en"), ur: body("ur") },
    buttons:
      step?.buttons.map((button) => ({
        intent: button.intent,
        labels: { en: button.labels.en ?? "", ur: button.labels.ur ?? "" },
      })) ?? [],
  };
}

export function toStepInput(
  values: SeriesStepFormValues,
  languages: SeriesLanguage[],
): SeriesStepInput {
  return {
    delay_days: values.delay_days,
    category: values.category,
    media_type: values.media_type,
    media_url: values.media_type === "none" ? null : values.media_url,
    contents: languages.map((language) => ({
      language,
      body: values.contents[language],
    })),
    buttons: values.buttons.map((button, index) => ({
      id: `btn_${button.intent}_${index + 1}`,
      intent: button.intent,
      labels: Object.fromEntries(
        languages.map((language) => [language, button.labels[language]]),
      ),
    })),
  };
}

export const variableTokens = [
  { label: "Donor name", value: "{{donor_name}}" },
  { label: "Center name", value: "{{center_name}}" },
  { label: "Appointment date", value: "{{appointment_date}}" },
] as const;
