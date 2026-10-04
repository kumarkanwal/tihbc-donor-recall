"use client";

import { Plus, Trash2 } from "lucide-react";
import { useFieldArray, type UseFormReturn } from "react-hook-form";

import type { SeriesStepFormValues } from "@/components/features/series/series-step-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { SeriesLanguage } from "@/hooks/use-content-series";

const selectClass =
  "border-border bg-surface text-foreground rounded-control h-10 border px-3 text-sm disabled:opacity-50";

/** Up to three localized deterministic quick-reply buttons. */
export function SeriesStepButtonsFields({
  form,
  languages,
  readOnly,
}: {
  form: UseFormReturn<SeriesStepFormValues>;
  languages: SeriesLanguage[];
  readOnly: boolean;
}): React.JSX.Element {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "buttons",
  });
  const atLimit = fields.length >= 3;
  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Quick-reply buttons</h3>
          <p className="text-muted-foreground text-xs">
            Add up to three response choices.
          </p>
        </div>
        {!readOnly ? (
          <Button
            type="button"
            size="small"
            variant="secondary"
            disabled={atLimit}
            onClick={() =>
              append({ intent: "confirm", labels: { en: "", ur: "" } })
            }
          >
            <Plus aria-hidden="true" />
            Add button
          </Button>
        ) : null}
      </div>
      <div className="mt-3 space-y-3">
        {fields.map((field, index) => (
          <div
            key={field.id}
            className="border-border rounded-card space-y-3 border p-3"
          >
            <div className="flex items-center gap-2">
              <label className="flex-1 text-xs font-medium">
                Intent
                <select
                  aria-label={`Button ${index + 1} intent`}
                  disabled={readOnly}
                  className={`${selectClass} mt-1 w-full`}
                  {...form.register(`buttons.${index}.intent`)}
                >
                  <option value="confirm">Confirm</option>
                  <option value="reschedule">Reschedule</option>
                  <option value="decline">Decline</option>
                </select>
              </label>
              {!readOnly ? (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  aria-label={`Remove button ${index + 1}`}
                  onClick={() => remove(index)}
                >
                  <Trash2 aria-hidden="true" />
                </Button>
              ) : null}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {languages.map((language) => (
                <label key={language} className="text-xs font-medium">
                  {language === "en" ? "English" : "Urdu"} label
                  <Input
                    className="mt-1"
                    maxLength={20}
                    disabled={readOnly}
                    aria-label={`Button ${index + 1} ${language === "en" ? "English" : "Urdu"} label`}
                    {...form.register(`buttons.${index}.labels.${language}`)}
                  />
                  <span className="mt-1 flex justify-between">
                    <span className="text-danger">
                      {
                        form.formState.errors.buttons?.[index]?.labels?.[
                          language
                        ]?.message
                      }
                    </span>
                    <span className="text-muted-foreground tabular-nums">
                      {form.watch(`buttons.${index}.labels.${language}`).length}
                      /20
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
      {atLimit ? (
        <p className="text-muted-foreground mt-2 text-xs">
          Maximum of 3 quick-reply buttons reached.
        </p>
      ) : null}
      {form.formState.errors.buttons?.message ? (
        <p className="text-danger mt-2 text-xs" role="alert">
          {form.formState.errors.buttons.message}
        </p>
      ) : null}
    </section>
  );
}
