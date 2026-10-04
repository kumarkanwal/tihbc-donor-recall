import { Trash2, Upload } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";

import type { SeriesStepFormValues } from "@/components/features/series/series-step-form";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { SeriesStep } from "@/hooks/use-content-series";

const selectClass =
  "border-border bg-surface text-foreground rounded-control focus-visible:outline-ring h-10 w-full border px-3 text-sm focus-visible:outline-2 disabled:opacity-50";

export function SeriesStepBasics({
  form,
  readOnly,
  uploadPending,
  onUpload,
}: {
  form: UseFormReturn<SeriesStepFormValues>;
  readOnly: boolean;
  uploadPending: boolean;
  onUpload: (file: File) => void;
}): React.JSX.Element {
  const mediaType = form.watch("media_type");
  const mediaUrl = form.watch("media_url");
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium">
          Delay days
          <Input
            type="number"
            min={0}
            max={365}
            className="mt-1.5"
            {...form.register("delay_days", { valueAsNumber: true })}
          />
        </label>
        <label className="text-sm font-medium">
          Category
          <select
            className={`${selectClass} mt-1.5`}
            {...form.register("category")}
          >
            <option value="utility">Utility</option>
            <option value="marketing">Marketing</option>
          </select>
        </label>
      </div>
      <section>
        <h3 className="text-sm font-semibold">Media</h3>
        {mediaUrl ? (
          <div className="border-border mt-2 flex items-center justify-between gap-3 rounded border p-3 text-sm">
            <span className="truncate">
              {mediaType === "video" ? "Video" : "Image"}: {mediaUrl}
            </span>
            {!readOnly ? (
              <Button
                type="button"
                size="small"
                variant="secondary"
                onClick={() => {
                  form.setValue("media_type", "none", { shouldDirty: true });
                  form.setValue("media_url", null, { shouldDirty: true });
                }}
              >
                Remove media
              </Button>
            ) : null}
          </div>
        ) : (
          <label className="border-border bg-surface-muted focus-within:outline-ring mt-2 flex cursor-pointer items-center justify-center gap-2 rounded border border-dashed p-4 text-sm focus-within:outline-2">
            <Upload aria-hidden="true" className="size-4" />
            {uploadPending ? "Uploading media" : "Upload image or MP4"}
            <input
              className="sr-only"
              type="file"
              accept="image/jpeg,image/png,image/webp,video/mp4"
              disabled={readOnly || uploadPending}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) onUpload(file);
              }}
            />
          </label>
        )}
      </section>
    </>
  );
}

export function SeriesStepDrawerFooter({
  step,
  readOnly,
  pending,
  uploadPending,
  deletePending,
  onClose,
  onDelete,
}: {
  step: SeriesStep | null;
  readOnly: boolean;
  pending: boolean;
  uploadPending: boolean;
  deletePending: boolean;
  onClose: () => void;
  onDelete: () => void;
}): React.JSX.Element {
  return (
    <div className="border-border flex flex-wrap justify-between gap-3 border-t pt-5">
      <div>
        {step && !readOnly ? (
          <ConfirmDialog
            title="Delete this step?"
            description="The remaining steps will be renumbered."
            confirmLabel="Delete step"
            destructive
            pending={deletePending}
            onConfirm={onDelete}
            trigger={
              <Button type="button" variant="destructive">
                <Trash2 aria-hidden="true" />
                Delete step
              </Button>
            }
          />
        ) : null}
      </div>
      <div className="flex gap-2">
        <Button type="button" variant="secondary" onClick={onClose}>
          Close
        </Button>
        {!readOnly ? (
          <Button type="submit" disabled={pending || uploadPending}>
            {pending ? "Saving" : "Save step"}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
