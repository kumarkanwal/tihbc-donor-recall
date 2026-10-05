"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  getCampaignErrorMessage,
  type CampaignCreate,
  type CampaignDetail,
  type CampaignLaunchProblem,
} from "@/hooks/use-campaigns";
import {
  useContentSeries,
  useContentSeriesDetail,
} from "@/hooks/use-content-series";
import { useDonorBatch, useDonorBatches } from "@/hooks/use-donor-batches";

import { CampaignFormFields } from "./campaign-form-fields";
import { CampaignFormActions } from "./campaign-form-actions";
import {
  campaignFormSchema,
  getCampaignFormDefaults,
  toCampaignInput,
  type CampaignFormValues,
} from "./campaign-form-model";
import { CampaignSummary } from "./campaign-summary";
import { LaunchProblems } from "./launch-problems";

interface CampaignFormProps {
  campaign?: CampaignDetail;
  readOnly?: boolean;
  pending?: boolean;
  error?: unknown;
  launchProblems?: CampaignLaunchProblem[];
  allowLaunch?: boolean;
  onSave: (input: CampaignCreate) => void;
  onLaunch?: (input: CampaignCreate) => void;
}

/** Validated campaign form with live audience and schedule summary. */
export function CampaignForm({
  campaign,
  readOnly = false,
  pending = false,
  error,
  launchProblems = [],
  allowLaunch = false,
  onSave,
  onLaunch,
}: CampaignFormProps): React.JSX.Element {
  const [batchSearch, setBatchSearch] = useState("");
  const [primarySearch, setPrimarySearch] = useState("");
  const [secondarySearch, setSecondarySearch] = useState("");
  const form = useForm<CampaignFormValues>({
    resolver: zodResolver(campaignFormSchema),
    defaultValues: getCampaignFormDefaults(campaign),
  });
  const [batchId = "", primaryId = "", secondaryId = ""] = useWatch({
    control: form.control,
    name: ["batch_id", "primary_series_id", "secondary_series_id"],
  });
  const batches = useDonorBatches({
    page: 1,
    page_size: 100,
    search: batchSearch || undefined,
    sort: "name",
  });
  const primarySeries = useContentSeries({
    page: 1,
    page_size: 100,
    search: primarySearch || undefined,
    kind: "primary",
    status: "active",
  });
  const secondarySeries = useContentSeries({
    page: 1,
    page_size: 100,
    search: secondarySearch || undefined,
    kind: "secondary",
    status: "active",
  });
  const batch = useDonorBatch(batchId);
  const primary = useContentSeriesDetail(primaryId);
  const secondary = useContentSeriesDetail(secondaryId);

  useEffect(() => {
    form.reset(getCampaignFormDefaults(campaign));
  }, [campaign, form]);

  const batchOptions =
    batches.data?.items.map((item) => ({
      value: item.id,
      label: `${item.name} · ${item.valid_rows} donors`,
    })) ?? [];
  const primaryOptions =
    primarySeries.data?.items.map((item) => ({
      value: item.id,
      label: item.name,
    })) ?? [];
  const secondaryOptions =
    secondarySeries.data?.items.map((item) => ({
      value: item.id,
      label: item.name,
    })) ?? [];
  const optionError =
    batches.error ?? primarySeries.error ?? secondarySeries.error;
  const optionsPending =
    batches.isPending || primarySeries.isPending || secondarySeries.isPending;

  return (
    <form
      onSubmit={form.handleSubmit((values) => onSave(toCampaignInput(values)))}
    >
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
        <section className="border-border bg-surface rounded-card border p-5">
          <h2 className="text-lg font-semibold">Campaign settings</h2>
          <p className="text-muted-foreground mt-1 mb-6 text-sm">
            Choose one donor audience and active primary and secondary
            sequences.
          </p>
          <CampaignFormFields
            form={form}
            batchOptions={batchOptions}
            primaryOptions={primaryOptions}
            secondaryOptions={secondaryOptions}
            disabled={readOnly || pending || optionsPending}
            onBatchSearch={setBatchSearch}
            onPrimarySearch={setPrimarySearch}
            onSecondarySearch={setSecondarySearch}
          />
          {optionsPending ? (
            <p className="text-muted-foreground mt-4 text-sm">
              Loading campaign options...
            </p>
          ) : null}
          {optionError ? (
            <div
              role="alert"
              className="text-danger mt-4 flex items-center justify-between gap-3 text-sm"
            >
              <span>Campaign options could not be loaded.</span>
              <Button
                type="button"
                variant="secondary"
                size="small"
                onClick={() => {
                  void batches.refetch();
                  void primarySeries.refetch();
                  void secondarySeries.refetch();
                }}
              >
                Try again
              </Button>
            </div>
          ) : null}
          {error ? (
            <p role="alert" className="text-danger mt-4 text-sm">
              {getCampaignErrorMessage(
                error,
                "The campaign could not be saved.",
              )}
            </p>
          ) : null}
          <div className="mt-6">
            <LaunchProblems problems={launchProblems} />
          </div>
          {!readOnly ? (
            <CampaignFormActions
              isExisting={Boolean(campaign)}
              allowLaunch={allowLaunch && Boolean(onLaunch)}
              pending={pending}
              onLaunch={() => {
                if (!onLaunch) return;
                void form.handleSubmit((values) =>
                  onLaunch(toCampaignInput(values)),
                )();
              }}
            />
          ) : null}
        </section>
        <CampaignSummary
          batch={batch.data}
          primary={primary.data}
          secondary={secondary.data}
        />
      </div>
    </form>
  );
}
