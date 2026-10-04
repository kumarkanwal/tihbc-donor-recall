"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { SeriesStepButtonsFields } from "@/components/features/series/series-step-buttons-fields";
import { SeriesStepContentFields } from "@/components/features/series/series-step-content-fields";
import {
  SeriesStepBasics,
  SeriesStepDrawerFooter,
} from "@/components/features/series/series-step-drawer-parts";
import { SeriesStepDrawerHeader } from "@/components/features/series/series-step-drawer-header";
import {
  getStepDefaults,
  stepFormSchema,
  toStepInput,
  type SeriesStepFormValues,
} from "@/components/features/series/series-step-form";
import {
  getContentSeriesErrorMessage,
  useCreateSeriesStep,
  useDeleteSeriesStep,
  useUpdateSeriesStep,
  useUploadSeriesMedia,
  type SeriesLanguage,
  type SeriesStep,
} from "@/hooks/use-content-series";

interface SeriesStepDrawerProps {
  open: boolean;
  seriesId: string;
  languages: SeriesLanguage[];
  step: SeriesStep | null;
  readOnly: boolean;
  onClose: () => void;
  onSaved: (step: SeriesStep) => void;
  onDeleted: () => void;
}

/** Drawer for creating, editing, or inspecting one ordered series step. */
export function SeriesStepDrawer({
  open,
  seriesId,
  languages,
  step,
  readOnly,
  onClose,
  onSaved,
  onDeleted,
}: SeriesStepDrawerProps): React.JSX.Element | null {
  const [language, setLanguage] = useState<SeriesLanguage>(
    languages[0] ?? "en",
  );
  const form = useForm<SeriesStepFormValues>({
    resolver: zodResolver(stepFormSchema),
    defaultValues: getStepDefaults(step ?? undefined),
  });
  const createStep = useCreateSeriesStep(seriesId);
  const updateStep = useUpdateSeriesStep(seriesId, step?.id ?? "");
  const deleteStep = useDeleteSeriesStep(seriesId);
  const uploadMedia = useUploadSeriesMedia();
  const mutationError =
    createStep.error ??
    updateStep.error ??
    uploadMedia.error ??
    deleteStep.error;
  const pending = createStep.isPending || updateStep.isPending;

  useEffect(() => {
    if (open) {
      form.reset(getStepDefaults(step ?? undefined));
    }
  }, [form, open, step]);

  async function submit(values: SeriesStepFormValues): Promise<void> {
    let valid = true;
    values.buttons.forEach((button, index) =>
      languages.forEach((code) => {
        if (!button.labels[code].trim()) {
          form.setError(`buttons.${index}.labels.${code}`, {
            message: "Enter a label.",
          });
          valid = false;
        }
      }),
    );
    if (!valid) return;
    try {
      const input = toStepInput(values, languages);
      const saved = step
        ? await updateStep.mutateAsync(input)
        : await createStep.mutateAsync(input);
      onSaved(saved);
      onClose();
    } catch {
      // The mutation error is rendered in the drawer.
    }
  }

  async function upload(file: File): Promise<void> {
    try {
      const media = await uploadMedia.mutateAsync(file);
      form.setValue("media_type", media.media_type, { shouldDirty: true });
      form.setValue("media_url", media.url, { shouldDirty: true });
    } catch {
      // The mutation error is rendered in the drawer.
    }
  }

  async function removeStep(): Promise<void> {
    if (!step) return;
    try {
      await deleteStep.mutateAsync(step.id);
      onDeleted();
      onClose();
    } catch {
      // The mutation error is rendered in the drawer.
    }
  }

  if (!open) return null;
  const effectiveLanguage = languages.includes(language)
    ? language
    : (languages[0] ?? "en");
  return (
    <div
      className="bg-foreground/20 fixed inset-0 z-50"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="step-drawer-title"
        className="border-border bg-surface absolute top-0 right-0 h-full w-full max-w-2xl overflow-y-auto border-l p-6 shadow-xl"
      >
        <SeriesStepDrawerHeader step={step} onClose={onClose} />
        <form
          className="mt-6 space-y-6"
          onSubmit={form.handleSubmit((values) => void submit(values))}
        >
          <fieldset disabled={readOnly || pending} className="space-y-6">
            <SeriesStepBasics
              form={form}
              readOnly={readOnly}
              uploadPending={uploadMedia.isPending}
              onUpload={(file) => void upload(file)}
            />
            <SeriesStepContentFields
              form={form}
              languages={languages}
              language={effectiveLanguage}
              onLanguageChange={setLanguage}
              readOnly={readOnly}
            />
            <SeriesStepButtonsFields
              form={form}
              languages={languages}
              readOnly={readOnly}
            />
          </fieldset>
          {mutationError ? (
            <p className="text-danger text-sm" role="alert">
              {getContentSeriesErrorMessage(
                mutationError,
                "The step could not be saved.",
              )}
            </p>
          ) : null}
          <SeriesStepDrawerFooter
            step={step}
            readOnly={readOnly}
            pending={pending}
            uploadPending={uploadMedia.isPending}
            deletePending={deleteStep.isPending}
            onClose={onClose}
            onDelete={() => void removeStep()}
          />
        </form>
      </aside>
    </div>
  );
}
