"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Download } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { downloadBlob } from "@/components/features/batches/batch-files";
import {
  ConfirmStep,
  ImportSuccess,
  InlineBatchError,
  ReviewStep,
  WizardProgress,
  type WizardStep,
} from "@/components/features/batches/batch-upload-steps";
import { FileDropzone } from "@/components/shared/file-dropzone";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useImportDonorBatch,
  usePreviewDonorBatch,
  useSampleBatchFile,
  type BatchPreview,
  type DonorBatch,
} from "@/hooks/use-donor-batches";

const uploadMaxBytes = 10 * 1024 * 1024;
const uploadSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Enter a batch name.")
    .max(120, "Use 120 characters or fewer."),
});
type UploadFormValues = z.infer<typeof uploadSchema>;

/** Three-step donor-batch validation and import flow. */
export function BatchUploadWizard(): React.JSX.Element {
  const [step, setStep] = useState<WizardStep>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BatchPreview | null>(null);
  const [importedBatch, setImportedBatch] = useState<DonorBatch | null>(null);
  const [dropzoneKey, setDropzoneKey] = useState(0);
  const form = useForm<UploadFormValues>({
    resolver: zodResolver(uploadSchema),
    defaultValues: { name: "" },
  });
  const previewBatch = usePreviewDonorBatch();
  const importBatch = useImportDonorBatch();
  const sampleFile = useSampleBatchFile();

  async function submitPreview(): Promise<void> {
    if (!file) return;
    try {
      const nextPreview = await previewBatch.mutateAsync(file);
      setPreview(nextPreview);
      setStep("review");
    } catch {
      // The mutation state owns the documented inline error.
    }
  }

  async function submitImport(): Promise<void> {
    if (!preview || preview.valid_rows === 0) return;
    try {
      const batch = await importBatch.mutateAsync({
        name: form.getValues("name").trim(),
        previewToken: preview.preview_token,
      });
      setImportedBatch(batch);
    } catch {
      // The mutation state owns the documented inline error.
    }
  }

  async function downloadSample(): Promise<void> {
    try {
      const blob = await sampleFile.mutateAsync();
      downloadBlob(blob, "tihbc-donor-batch-sample.csv");
    } catch {
      // The mutation state owns the documented inline error.
    }
  }

  function resetWizard(): void {
    setStep("upload");
    setFile(null);
    setPreview(null);
    setImportedBatch(null);
    setDropzoneKey((value) => value + 1);
    previewBatch.reset();
    importBatch.reset();
  }

  if (importedBatch) {
    return <ImportSuccess batch={importedBatch} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload donor batch"
        description="Validate donor details before importing them into TIHBC Donor Recall."
        breadcrumb={<Link href="/batches">Donor Batches</Link>}
      />
      <WizardProgress currentStep={step} />

      {step === "upload" ? (
        <form className="space-y-6" onSubmit={form.handleSubmit(submitPreview)}>
          <section className="border-border bg-surface rounded-card space-y-5 border p-6">
            <div>
              <label htmlFor="batch-name" className="text-sm font-medium">
                Batch name
              </label>
              <Input
                id="batch-name"
                className="mt-2 max-w-xl"
                maxLength={120}
                placeholder="October regular donor recall"
                aria-invalid={Boolean(form.formState.errors.name)}
                {...form.register("name")}
              />
              {form.formState.errors.name ? (
                <p className="text-danger mt-2 text-sm" role="alert">
                  {form.formState.errors.name.message}
                </p>
              ) : null}
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between gap-4">
                <span className="text-sm font-medium">Donor file</span>
                <button
                  type="button"
                  className="text-primary focus-visible:outline-ring inline-flex items-center gap-2 rounded text-sm font-medium underline-offset-4 hover:underline focus-visible:outline-2"
                  disabled={sampleFile.isPending}
                  onClick={() => void downloadSample()}
                >
                  <Download aria-hidden="true" className="size-4" />
                  {sampleFile.isPending
                    ? "Downloading"
                    : "Download sample file"}
                </button>
              </div>
              <FileDropzone
                key={dropzoneKey}
                accept=".csv,.xlsx"
                maxSize={uploadMaxBytes}
                onFileSelect={setFile}
                disabled={previewBatch.isPending}
              />
            </div>
            <InlineBatchError
              error={sampleFile.error}
              fallback="The sample file could not be downloaded."
            />
            <InlineBatchError
              error={previewBatch.error}
              fallback="The donor file could not be reviewed."
            />
          </section>
          <div className="flex justify-end">
            <Button type="submit" disabled={!file || previewBatch.isPending}>
              {previewBatch.isPending ? "Validating file" : "Review batch"}
            </Button>
          </div>
        </form>
      ) : null}

      {step === "review" && preview ? (
        <ReviewStep
          preview={preview}
          onBack={() => setStep("upload")}
          onContinue={() => setStep("confirm")}
        />
      ) : null}

      {step === "confirm" && preview ? (
        <ConfirmStep
          preview={preview}
          batchName={form.getValues("name").trim()}
          error={importBatch.error}
          pending={importBatch.isPending}
          onBack={() => setStep("review")}
          onConfirm={() => void submitImport()}
          onUploadAgain={resetWizard}
        />
      ) : null}
    </div>
  );
}
