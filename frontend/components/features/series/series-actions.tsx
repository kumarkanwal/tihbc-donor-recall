"use client";

import { Archive, Copy, ExternalLink } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";
import { useCan } from "@/hooks/use-can";
import {
  getContentSeriesErrorMessage,
  useArchiveContentSeries,
  useDuplicateContentSeries,
  type ContentSeries,
} from "@/hooks/use-content-series";

/** Open and administrator-only lifecycle actions for a series. */
export function SeriesActions({
  series,
  compact = false,
}: {
  series: ContentSeries;
  compact?: boolean;
}): React.JSX.Element {
  const canManage = useCan(["admin"]);
  const router = useRouter();
  const duplicateSeries = useDuplicateContentSeries();
  const archiveSeries = useArchiveContentSeries();
  const error = duplicateSeries.error ?? archiveSeries.error;

  async function duplicate(): Promise<void> {
    try {
      const copy = await duplicateSeries.mutateAsync(series.id);
      router.push(`/series/${copy.id}`);
    } catch {
      // Mutation error is shown beside the actions.
    }
  }

  return (
    <div
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <div className="flex flex-wrap gap-2">
        <Button asChild variant="secondary" size="small">
          <Link href={`/series/${series.id}`}>
            <ExternalLink aria-hidden="true" />
            {compact ? "Open" : "Open series"}
          </Link>
        </Button>
        {canManage ? (
          <Button
            type="button"
            variant="secondary"
            size="small"
            disabled={duplicateSeries.isPending}
            onClick={() => void duplicate()}
          >
            <Copy aria-hidden="true" />
            Duplicate
          </Button>
        ) : null}
        {canManage && series.status !== "archived" ? (
          <ConfirmDialog
            title="Archive content series?"
            description={`${series.name} will become read-only and cannot be activated again.`}
            confirmLabel="Archive series"
            destructive
            pending={archiveSeries.isPending}
            onConfirm={() => archiveSeries.mutate(series.id)}
            trigger={
              <Button type="button" variant="secondary" size="small">
                <Archive aria-hidden="true" />
                Archive
              </Button>
            }
          />
        ) : null}
      </div>
      {error ? (
        <p className="text-danger mt-2 max-w-xs text-xs" role="alert">
          {getContentSeriesErrorMessage(
            error,
            "The series action could not be completed.",
          )}
        </p>
      ) : null}
    </div>
  );
}
