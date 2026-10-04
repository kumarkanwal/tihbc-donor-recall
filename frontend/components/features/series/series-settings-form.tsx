"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { SeriesSettingsFields } from "@/components/features/series/series-settings-fields";
import { Button } from "@/components/ui/button";
import {
  getContentSeriesErrorMessage,
  type ContentSeriesCreate,
  type ContentSeriesDetail,
} from "@/hooks/use-content-series";

const settingsSchema = z.object({
  name: z.string().trim().min(1, "Enter a series name.").max(120),
  description: z.string().trim().max(500),
  kind: z.enum(["primary", "secondary"]),
  languages: z
    .array(z.enum(["en", "ur"]))
    .min(1, "Select at least one language."),
  response_window_hours: z
    .number()
    .int()
    .min(1, "Enter at least 1 hour.")
    .max(720),
  tags: z.string(),
});

export type SeriesSettingsValues = z.infer<typeof settingsSchema>;

export function getSeriesSettingsDefaults(
  series?: ContentSeriesDetail,
): SeriesSettingsValues {
  return {
    name: series?.name ?? "",
    description: series?.description ?? "",
    kind: series?.kind ?? "primary",
    languages: series?.languages ?? ["en", "ur"],
    response_window_hours: series?.response_window_hours ?? 48,
    tags: series?.tags.join(", ") ?? "",
  };
}

export function toSeriesInput(
  values: SeriesSettingsValues,
): ContentSeriesCreate {
  return {
    name: values.name.trim(),
    description: values.description.trim() || null,
    kind: values.kind,
    languages: values.languages,
    response_window_hours: values.response_window_hours,
    tag_names: values.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
  };
}

interface SeriesSettingsFormProps {
  series?: ContentSeriesDetail;
  readOnly?: boolean;
  pending?: boolean;
  error?: unknown;
  submitLabel?: string;
  onSubmit: (values: SeriesSettingsValues) => void;
}

/** Validated content-series settings used by create and edit flows. */
export function SeriesSettingsForm({
  series,
  readOnly = false,
  pending = false,
  error,
  submitLabel = "Save settings",
  onSubmit,
}: SeriesSettingsFormProps): React.JSX.Element {
  const form = useForm<SeriesSettingsValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: getSeriesSettingsDefaults(series),
  });
  useEffect(() => {
    form.reset(getSeriesSettingsDefaults(series));
  }, [form, series]);
  return (
    <form
      className="border-border bg-surface rounded-card border p-5"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <SeriesSettingsFields form={form} disabled={readOnly || pending} />
      {error ? (
        <p className="text-danger mt-4 text-sm" role="alert">
          {getContentSeriesErrorMessage(
            error,
            "The series settings could not be saved.",
          )}
        </p>
      ) : null}
      {!readOnly ? (
        <div className="mt-5 flex justify-end">
          <Button type="submit" disabled={pending}>
            {pending ? "Saving" : submitLabel}
          </Button>
        </div>
      ) : null}
    </form>
  );
}
