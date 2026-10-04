import { Download } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";

import { InlineBatchError } from "@/components/features/batches/batch-upload-steps";
import { FileDropzone } from "@/components/shared/file-dropzone";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface BatchUploadFormValues {
  name: string;
}

interface BatchUploadFormProps {
  form: UseFormReturn<BatchUploadFormValues>;
  file: File | null;
  dropzoneKey: number;
  previewPending: boolean;
  previewError: unknown;
  samplePending: boolean;
  sampleError: unknown;
  onFileSelect: (file: File) => void;
  onDownloadSample: () => void;
  onSubmit: () => void;
}

const uploadMaxBytes = 10 * 1024 * 1024;

/** Initial donor-file selection and validation form. */
export function BatchUploadForm({
  form,
  file,
  dropzoneKey,
  previewPending,
  previewError,
  samplePending,
  sampleError,
  onFileSelect,
  onDownloadSample,
  onSubmit,
}: BatchUploadFormProps): React.JSX.Element {
  return (
    <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
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
              disabled={samplePending}
              onClick={onDownloadSample}
            >
              <Download aria-hidden="true" className="size-4" />
              {samplePending ? "Downloading" : "Download sample file"}
            </button>
          </div>
          <FileDropzone
            key={dropzoneKey}
            accept=".csv,.xlsx"
            maxSize={uploadMaxBytes}
            onFileSelect={onFileSelect}
            disabled={previewPending}
          />
        </div>
        <InlineBatchError
          error={sampleError}
          fallback="The sample file could not be downloaded."
        />
        <InlineBatchError
          error={previewError}
          fallback="The donor file could not be reviewed."
        />
      </section>
      <div className="flex justify-end">
        <Button type="submit" disabled={!file || previewPending}>
          {previewPending ? "Validating file" : "Review batch"}
        </Button>
      </div>
    </form>
  );
}
