import { useWatch, type UseFormReturn } from "react-hook-form";

import { Input } from "@/components/ui/input";

import type { CampaignFormValues } from "./campaign-form-model";
import {
  CampaignSearchableSelect,
  type CampaignSelectOption,
} from "./campaign-searchable-select";

interface CampaignFormFieldsProps {
  form: UseFormReturn<CampaignFormValues>;
  batchOptions: CampaignSelectOption[];
  primaryOptions: CampaignSelectOption[];
  secondaryOptions: CampaignSelectOption[];
  disabled: boolean;
  onBatchSearch: (value: string) => void;
  onPrimarySearch: (value: string) => void;
  onSecondarySearch: (value: string) => void;
}

/** Editable campaign settings shared by create and draft-detail flows. */
export function CampaignFormFields({
  form,
  batchOptions,
  primaryOptions,
  secondaryOptions,
  disabled,
  onBatchSearch,
  onPrimarySearch,
  onSecondarySearch,
}: CampaignFormFieldsProps): React.JSX.Element {
  const errors = form.formState.errors;
  const [batchId = "", primaryId = "", secondaryId = "", mode = "now"] =
    useWatch({
      control: form.control,
      name: [
        "batch_id",
        "primary_series_id",
        "secondary_series_id",
        "start_mode",
      ],
    });
  return (
    <fieldset disabled={disabled} className="space-y-5">
      <label className="block text-sm font-medium">
        Campaign name
        <Input
          className="mt-2"
          data-testid="campaign-name-input"
          {...form.register("name")}
        />
        {errors.name ? (
          <span className="text-danger mt-1 block text-xs">
            {errors.name.message}
          </span>
        ) : null}
      </label>
      <CampaignSearchableSelect
        id="campaign-batch"
        label="Donor batch"
        value={batchId}
        options={batchOptions}
        disabled={disabled}
        error={errors.batch_id?.message}
        onChange={(value) =>
          form.setValue("batch_id", value, { shouldValidate: true })
        }
        onSearchChange={onBatchSearch}
      />
      <CampaignSearchableSelect
        id="campaign-primary-series"
        label="Primary series"
        value={primaryId}
        options={primaryOptions}
        disabled={disabled}
        error={errors.primary_series_id?.message}
        onChange={(value) =>
          form.setValue("primary_series_id", value, { shouldValidate: true })
        }
        onSearchChange={onPrimarySearch}
      />
      <CampaignSearchableSelect
        id="campaign-secondary-series"
        label="Secondary series"
        value={secondaryId}
        options={secondaryOptions}
        disabled={disabled}
        error={errors.secondary_series_id?.message}
        onChange={(value) =>
          form.setValue("secondary_series_id", value, { shouldValidate: true })
        }
        onSearchChange={onSecondarySearch}
      />
      <div>
        <p className="text-sm font-medium">Start</p>
        <div className="mt-2 flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input type="radio" value="now" {...form.register("start_mode")} />
            Now
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              value="scheduled"
              {...form.register("start_mode")}
            />
            Choose date and time
          </label>
        </div>
        {mode === "scheduled" ? (
          <label className="mt-3 block text-sm">
            Start date and time (Asia/Karachi)
            <Input
              type="datetime-local"
              className="mt-2"
              {...form.register("start_local")}
            />
          </label>
        ) : null}
        {errors.start_local ? (
          <p className="text-danger mt-1 text-xs">
            {errors.start_local.message}
          </p>
        ) : null}
      </div>
    </fieldset>
  );
}
