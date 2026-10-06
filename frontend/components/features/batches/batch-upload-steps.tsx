import { AlertCircle, CheckCircle2 } from "lucide-react";
import Link from "next/link";

import { BatchBreakdowns } from "@/components/features/batches/batch-breakdowns";
import { BatchWarnings } from "@/components/features/batches/batch-warnings";
import { PreviewDonorsTable } from "@/components/features/batches/preview-donors-table";
import { ValidationIssuesTable } from "@/components/features/batches/validation-issues-table";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { KpiCard } from "@/components/shared/kpi-card";
import { Button } from "@/components/ui/button";
import {
  getDonorBatchErrorMessage,
  type BatchPreview,
  type DonorBatch,
} from "@/hooks/use-donor-batches";
import { ApiError } from "@/lib/api/errors";

export type WizardStep = "upload" | "review" | "confirm";
const steps: { id: WizardStep; label: string }[] = [
  { id: "upload", label: "Upload" },
  { id: "review", label: "Review" },
  { id: "confirm", label: "Confirm" },
];

export function WizardProgress({
  currentStep,
}: {
  currentStep: WizardStep;
}): React.JSX.Element {
  const currentIndex = steps.findIndex(({ id }) => id === currentStep);
  return (
    <ol
      className="border-border bg-surface rounded-card grid grid-cols-3 border p-2"
      aria-label="Upload progress"
    >
      {steps.map(({ id, label }, index) => (
        <li
          key={id}
          aria-current={id === currentStep ? "step" : undefined}
          className={`rounded-control px-3 py-2 text-center text-sm font-medium ${index <= currentIndex ? "bg-primary-soft text-primary" : "text-muted-foreground"}`}
        >
          {index + 1}. {label}
        </li>
      ))}
    </ol>
  );
}

export function InlineBatchError({
  error,
  fallback,
}: {
  error: unknown;
  fallback: string;
}): React.JSX.Element | null {
  if (!error) return null;
  return (
    <p className="text-danger flex items-start gap-2 text-sm" role="alert">
      <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      {getDonorBatchErrorMessage(error, fallback)}
    </p>
  );
}

export function ImportSuccess({
  batch,
}: {
  batch: DonorBatch;
}): React.JSX.Element {
  return (
    <section
      data-testid="batch-import-success"
      className="border-border bg-surface rounded-card mx-auto max-w-2xl border p-8 text-center"
    >
      <CheckCircle2
        className="text-success mx-auto size-10"
        aria-hidden="true"
      />
      <h1 className="mt-4 text-2xl font-semibold">Batch imported</h1>
      <p className="text-muted-foreground mt-2">
        {batch.valid_rows} valid donors were added to {batch.name}.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Button asChild>
          <Link href={`/batches/${batch.id}`}>View batch</Link>
        </Button>
        <Button asChild variant="secondary">
          <Link
            href="/campaigns/new"
            data-testid="batch-create-campaign-action"
          >
            Create campaign
          </Link>
        </Button>
      </div>
    </section>
  );
}

export function ReviewStep({
  preview,
  onBack,
  onContinue,
}: {
  preview: BatchPreview;
  onBack: () => void;
  onContinue: () => void;
}): React.JSX.Element {
  return (
    <div className="space-y-6" data-testid="batch-review-step">
      <div className="grid gap-4 sm:grid-cols-3">
        <KpiCard
          testId="batch-review-total-rows"
          label="Total rows"
          value={preview.total_rows}
        />
        <KpiCard
          testId="batch-review-valid-rows"
          label="Valid rows"
          value={preview.valid_rows}
        />
        <KpiCard
          testId="batch-review-invalid-rows"
          label="Invalid rows"
          value={preview.invalid_rows}
        />
      </div>
      <BatchBreakdowns {...preview} />
      <BatchWarnings warnings={preview.warnings} />
      <PreviewDonorsTable donors={preview.sample_valid_rows} />
      <ValidationIssuesTable issues={preview.errors} allowDownload />
      <div className="flex justify-between gap-3">
        <Button type="button" variant="secondary" onClick={onBack}>
          Back
        </Button>
        <Button
          type="button"
          data-testid="batch-review-continue"
          onClick={onContinue}
        >
          Continue to confirm
        </Button>
      </div>
    </div>
  );
}

export function ConfirmStep({
  preview,
  batchName,
  error,
  pending,
  onBack,
  onConfirm,
  onUploadAgain,
}: {
  preview: BatchPreview;
  batchName: string;
  error: unknown;
  pending: boolean;
  onBack: () => void;
  onConfirm: () => void;
  onUploadAgain: () => void;
}): React.JSX.Element {
  const previewExpired =
    error instanceof ApiError && error.code === "PREVIEW_EXPIRED";
  return (
    <section
      data-testid="batch-confirm-step"
      className="border-border bg-surface rounded-card border p-6"
    >
      <h2 className="text-lg font-semibold">Confirm import</h2>
      <p className="text-muted-foreground mt-2 text-sm">
        Import {preview.valid_rows} valid donors into{" "}
        <span className="text-foreground font-medium">{batchName}</span>.
        Invalid rows will remain in the validation report.
      </p>
      {preview.valid_rows === 0 ? (
        <p className="text-danger mt-4 text-sm" role="alert">
          This file has no valid donor rows. Correct the errors and upload it
          again before importing.
        </p>
      ) : null}
      <InlineBatchError
        error={error}
        fallback="The donor batch could not be imported."
      />
      <div className="mt-6 flex flex-wrap justify-between gap-3">
        <Button
          type="button"
          variant="secondary"
          onClick={onBack}
          disabled={pending}
        >
          Back
        </Button>
        <div className="flex gap-3">
          {previewExpired ? (
            <Button type="button" variant="secondary" onClick={onUploadAgain}>
              Upload again
            </Button>
          ) : null}
          <ConfirmDialog
            title="Import donor batch?"
            description={`This will import ${preview.valid_rows} valid donors into ${batchName}.`}
            confirmLabel={`Import ${preview.valid_rows} valid donors`}
            pending={pending}
            onConfirm={onConfirm}
            trigger={
              <Button
                type="button"
                data-testid="batch-import-trigger"
                disabled={preview.valid_rows === 0 || pending || previewExpired}
              >
                Import {preview.valid_rows} valid donors
              </Button>
            }
          />
        </div>
      </div>
    </section>
  );
}
