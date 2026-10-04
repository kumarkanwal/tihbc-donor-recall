"use client";

import type { UseFormReturn } from "react-hook-form";

import {
  variableTokens,
  type SeriesStepFormValues,
} from "@/components/features/series/series-step-form";
import { LanguageTabs } from "@/components/shared/language-tabs";
import { Button } from "@/components/ui/button";
import type { SeriesLanguage } from "@/hooks/use-content-series";

interface SeriesStepContentFieldsProps {
  form: UseFormReturn<SeriesStepFormValues>;
  languages: SeriesLanguage[];
  language: SeriesLanguage;
  onLanguageChange: (language: SeriesLanguage) => void;
  readOnly: boolean;
}

/** Localized body fields and caret-aware variable insertion. */
export function SeriesStepContentFields({
  form,
  languages,
  language,
  onLanguageChange,
  readOnly,
}: SeriesStepContentFieldsProps): React.JSX.Element {
  const renderEditor = (code: SeriesLanguage) => {
    const registration = form.register(`contents.${code}`);
    const value = form.watch(`contents.${code}`);
    const insertVariable = (token: string) => {
      const element = document.getElementById(
        `series-step-body-${code}`,
      ) as HTMLTextAreaElement | null;
      const start = element?.selectionStart ?? value.length;
      const end = element?.selectionEnd ?? start;
      const next = `${value.slice(0, start)}${token}${value.slice(end)}`;
      form.setValue(`contents.${code}`, next, {
        shouldDirty: true,
        shouldValidate: true,
      });
      requestAnimationFrame(() => {
        element?.focus();
        element?.setSelectionRange(start + token.length, start + token.length);
      });
    };
    return (
      <div>
        <div className="flex flex-wrap gap-2">
          {variableTokens.map((variable) => (
            <Button
              key={variable.value}
              type="button"
              size="small"
              variant="secondary"
              disabled={readOnly}
              onClick={() => insertVariable(variable.value)}
            >
              Insert {variable.label}
            </Button>
          ))}
        </div>
        <textarea
          aria-label={`${code === "en" ? "English" : "Urdu"} message body`}
          id={`series-step-body-${code}`}
          rows={7}
          maxLength={1024}
          disabled={readOnly}
          className="border-border bg-surface text-foreground rounded-control focus-visible:outline-ring mt-3 w-full border px-3 py-2 text-sm focus-visible:outline-2 disabled:opacity-60"
          {...registration}
        />
        <div className="mt-1 flex justify-between text-xs">
          <span className="text-danger">
            {form.formState.errors.contents?.[code]?.message}
          </span>
          <span className="text-muted-foreground tabular-nums">
            {value.length}/1024
          </span>
        </div>
      </div>
    );
  };

  return (
    <div>
      <h3 className="text-sm font-semibold">Message content</h3>
      <LanguageTabs
        languages={languages}
        value={language}
        onValueChange={onLanguageChange}
        english={renderEditor("en")}
        urdu={renderEditor("ur")}
      />
    </div>
  );
}
