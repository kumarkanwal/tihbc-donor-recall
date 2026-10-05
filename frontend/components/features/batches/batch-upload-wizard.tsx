"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  ConfirmStep,
  ImportSuccess,
  ReviewStep,
  WizardProgress,
  type WizardStep,
} from "@/components/features/batches/batch-upload-steps";
import {
  BatchUploadForm,
  type BatchUploadFormValues,
} from "@/components/features/batches/batch-upload-form";
import { PageHeader } from "@/components/shared/page-header";
import { downloadBlob } from "@/lib/utils/download";
import {
  useImportDonorBatch,
  usePreviewDonorBatch,
  useSampleBatchFile,
  type BatchPreview,
  type DonorBatch,
} from "@/hooks/use-donor-batches";

const uploadSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Enter a batch name.")
    .max(120, "Use 120 characters or fewer."),
});

/** Three-step donor-batch validation and import flow. */
export function BatchUploadWizard(): React.JSX.Element {
  const [step, setStep] = useState<WizardStep>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BatchPreview | null>(null);
  const [importedBatch, setImportedBatch] = useState<DonorBatch | null>(null);
  const [dropzoneKey, setDropzoneKey] = useState(0);
  const form = useForm<BatchUploadFormValues>({
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
        <BatchUploadForm
          form={form}
          file={file}
          dropzoneKey={dropzoneKey}
          previewPending={previewBatch.isPending}
          previewError={previewBatch.error}
          samplePending={sampleFile.isPending}
          sampleError={sampleFile.error}
          onFileSelect={setFile}
          onDownloadSample={() => void downloadSample()}
          onSubmit={() => void submitPreview()}
        />
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
