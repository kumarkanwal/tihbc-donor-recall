import type { UseFormReturn } from "react-hook-form";

import type { SeriesSettingsValues } from "@/components/features/series/series-settings-form";
import { Input } from "@/components/ui/input";

const labelClass = "text-sm font-medium";
const selectClass =
  "border-border bg-surface text-foreground rounded-control focus-visible:outline-ring h-10 w-full border px-3 text-sm focus-visible:outline-2 disabled:cursor-not-allowed disabled:opacity-50";

/** Shared validated fields for series creation and settings updates. */
export function SeriesSettingsFields({
  form,
  disabled,
}: {
  form: UseFormReturn<SeriesSettingsValues>;
  disabled: boolean;
}): React.JSX.Element {
  return (
    <fieldset disabled={disabled} className="space-y-4">
      <legend className="text-lg font-semibold">Series settings</legend>
      <div>
        <label htmlFor="series-name" className={labelClass}>
          Name
        </label>
        <Input
          id="series-name"
          className="mt-1.5"
          maxLength={120}
          {...form.register("name")}
        />
        <FieldError message={form.formState.errors.name?.message} />
      </div>
      <div>
        <label htmlFor="series-description" className={labelClass}>
          Description
        </label>
        <textarea
          id="series-description"
          rows={3}
          maxLength={500}
          className="border-border bg-surface text-foreground rounded-control focus-visible:outline-ring mt-1.5 w-full border px-3 py-2 text-sm focus-visible:outline-2 disabled:opacity-50"
          {...form.register("description")}
        />
        <FieldError message={form.formState.errors.description?.message} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="series-kind" className={labelClass}>
            Kind
          </label>
          <select
            id="series-kind"
            className={`${selectClass} mt-1.5`}
            {...form.register("kind")}
          >
            <option value="primary">Primary</option>
            <option value="secondary">Secondary</option>
          </select>
        </div>
        <div>
          <label htmlFor="response-window" className={labelClass}>
            Response window (hours)
          </label>
          <Input
            id="response-window"
            className="mt-1.5"
            type="number"
            min={1}
            max={720}
            {...form.register("response_window_hours", { valueAsNumber: true })}
          />
          <FieldError
            message={form.formState.errors.response_window_hours?.message}
          />
        </div>
      </div>
      <div>
        <span className={labelClass}>Languages</span>
        <div className="mt-2 flex gap-5">
          <label className="flex items-center gap-2">
            <input type="checkbox" value="en" {...form.register("languages")} />{" "}
            English
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" value="ur" {...form.register("languages")} />{" "}
            Urdu
          </label>
        </div>
        <FieldError message={form.formState.errors.languages?.message} />
      </div>
      <div>
        <label htmlFor="series-tags" className={labelClass}>
          Tags
        </label>
        <Input
          id="series-tags"
          className="mt-1.5"
          placeholder="regular, recall"
          {...form.register("tags")}
        />
        <p className="text-muted-foreground mt-1 text-xs">
          Separate tags with commas.
        </p>
      </div>
    </fieldset>
  );
}

function FieldError({
  message,
}: {
  message?: string;
}): React.JSX.Element | null {
  return message ? (
    <p className="text-danger mt-1 text-xs" role="alert">
      {message}
    </p>
  ) : null;
}
