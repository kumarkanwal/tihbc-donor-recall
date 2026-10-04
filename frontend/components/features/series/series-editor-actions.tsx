"use client";

import { Archive, Check, Copy } from "lucide-react";
import { useRouter } from "next/navigation";

import { ActivationProblems } from "@/components/features/series/activation-problems";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";
import {
  getActivationProblems,
  getContentSeriesErrorMessage,
  useActivateContentSeries,
  useArchiveContentSeries,
  useDuplicateContentSeries,
  type ContentSeriesDetail,
} from "@/hooks/use-content-series";

/** Administrator lifecycle controls and structured activation feedback. */
export function SeriesEditorActions({
  series,
}: {
  series: ContentSeriesDetail;
}): React.JSX.Element {
  const router = useRouter();
  const activate = useActivateContentSeries();
  const duplicate = useDuplicateContentSeries();
  const archive = useArchiveContentSeries();
  const error = activate.error ?? duplicate.error ?? archive.error;
  const problems = getActivationProblems(activate.error);

  async function duplicateSeries(): Promise<void> {
    try {
      const copy = await duplicate.mutateAsync(series.id);
      router.push(`/series/${copy.id}`);
    } catch {
      // Mutation feedback is rendered below the controls.
    }
  }

  return (
    <div className="max-w-xl">
      <div className="flex flex-wrap justify-end gap-2">
        {series.status === "draft" ? (
          <Button
            type="button"
            disabled={activate.isPending}
            onClick={() => activate.mutate(series.id)}
          >
            <Check aria-hidden="true" />
            {activate.isPending ? "Activating" : "Activate series"}
          </Button>
        ) : null}
        <Button
          type="button"
          variant="secondary"
          disabled={duplicate.isPending}
          onClick={() => void duplicateSeries()}
        >
          <Copy aria-hidden="true" />
          Duplicate
        </Button>
        {series.status !== "archived" ? (
          <ConfirmDialog
            title="Archive content series?"
            description="Archived series are read-only and cannot be activated again."
            confirmLabel="Archive series"
            destructive
            pending={archive.isPending}
            onConfirm={() => archive.mutate(series.id)}
            trigger={
              <Button type="button" variant="secondary">
                <Archive aria-hidden="true" />
                Archive
              </Button>
            }
          />
        ) : null}
      </div>
      {error && !problems.length ? (
        <p className="text-danger mt-2 text-right text-sm" role="alert">
          {getContentSeriesErrorMessage(
            error,
            "The series action could not be completed.",
          )}
        </p>
      ) : null}
      <ActivationProblems problems={problems} />
    </div>
  );
}
