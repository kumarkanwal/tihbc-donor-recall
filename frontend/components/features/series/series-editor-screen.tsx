"use client";

import Link from "next/link";
import { useState } from "react";

import { SeriesEditorActions } from "@/components/features/series/series-editor-actions";
import { SeriesPreviewPanel } from "@/components/features/series/series-preview-panel";
import {
  SeriesSettingsForm,
  toSeriesInput,
  type SeriesSettingsValues,
} from "@/components/features/series/series-settings-form";
import { SeriesStepDrawer } from "@/components/features/series/series-step-drawer";
import { SeriesStepList } from "@/components/features/series/series-step-list";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { useCan } from "@/hooks/use-can";
import {
  getContentSeriesErrorMessage,
  useContentSeriesDetail,
  useReorderSeriesSteps,
  useUpdateContentSeries,
  type SeriesLanguage,
  type SeriesStep,
} from "@/hooks/use-content-series";

/** Two-column content-series editor with server-rendered phone preview. */
export function SeriesEditorScreen({
  seriesId,
  initialStepId,
}: {
  seriesId: string;
  initialStepId?: string;
}): React.JSX.Element {
  const canManage = useCan(["admin"]);
  const seriesQuery = useContentSeriesDetail(seriesId);
  const updateSeries = useUpdateContentSeries(seriesId);
  const reorderSteps = useReorderSeriesSteps(seriesId);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(
    initialStepId ?? null,
  );
  const [drawerStep, setDrawerStep] = useState<SeriesStep | null | undefined>(
    undefined,
  );
  const [previewLanguage, setPreviewLanguage] = useState<SeriesLanguage>("en");
  const series = seriesQuery.data;

  if (seriesQuery.isPending) return <SeriesEditorLoading />;
  if (seriesQuery.error || !series)
    return (
      <ErrorState
        title="Could not load series"
        description={getContentSeriesErrorMessage(
          seriesQuery.error,
          "The content series could not be loaded.",
        )}
        onRetry={() => void seriesQuery.refetch()}
      />
    );

  const readOnly = !canManage || series.status === "archived";
  async function saveSettings(values: SeriesSettingsValues): Promise<void> {
    try {
      await updateSeries.mutateAsync(toSeriesInput(values));
    } catch {
      /* Mutation error is inline. */
    }
  }
  const openStep = (step: SeriesStep) => {
    setSelectedStepId(step.id);
    setDrawerStep(step);
  };
  const selectedStep =
    series.steps.find((step) => step.id === selectedStepId) ??
    series.steps[0] ??
    null;
  const effectivePreviewLanguage = series.languages.includes(previewLanguage)
    ? previewLanguage
    : (series.languages[0] ?? "en");

  return (
    <div className="space-y-6">
      <PageHeader
        title={series.name}
        description={`${series.step_count} ${series.step_count === 1 ? "step" : "steps"} · ${series.response_window_hours}-hour response window`}
        breadcrumb={<Link href="/series">Content Series</Link>}
        actions={
          canManage ? (
            <SeriesEditorActions series={series} />
          ) : (
            <StatusBadge status={series.status} />
          )
        }
      />
      <SeriesEditorNotice status={series.status} canManage={canManage} />
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
        <div className="space-y-6">
          <SeriesSettingsForm
            series={series}
            readOnly={readOnly}
            pending={updateSeries.isPending}
            error={updateSeries.error}
            onSubmit={(values) => void saveSettings(values)}
          />
          <SeriesStepList
            steps={series.steps}
            selectedStepId={selectedStep?.id ?? null}
            readOnly={readOnly}
            pending={reorderSteps.isPending}
            onSelect={openStep}
            onAdd={() => setDrawerStep(null)}
            onReorder={(ids) => reorderSteps.mutate(ids)}
          />
          {reorderSteps.error ? (
            <p className="text-danger text-sm" role="alert">
              {getContentSeriesErrorMessage(
                reorderSteps.error,
                "The steps could not be reordered.",
              )}
            </p>
          ) : null}
        </div>
        <SeriesPreviewPanel
          seriesId={series.id}
          stepId={selectedStep?.id ?? null}
          languages={series.languages}
          language={effectivePreviewLanguage}
          onLanguageChange={setPreviewLanguage}
        />
      </div>
      <SeriesStepDrawer
        open={drawerStep !== undefined}
        seriesId={series.id}
        languages={series.languages}
        step={drawerStep ?? null}
        readOnly={readOnly}
        onClose={() => setDrawerStep(undefined)}
        onSaved={(step) => setSelectedStepId(step.id)}
        onDeleted={() => setSelectedStepId(null)}
      />
    </div>
  );
}

function SeriesEditorNotice({
  status,
  canManage,
}: {
  status: "draft" | "active" | "archived";
  canManage: boolean;
}): React.JSX.Element | null {
  if (!canManage)
    return (
      <p className="border-info/30 bg-info/10 text-info rounded-card border px-4 py-3 text-sm">
        Coordinator view: this content series is read-only.
      </p>
    );
  if (status === "archived")
    return (
      <p className="border-border bg-surface-muted text-muted-foreground rounded-card border px-4 py-3 text-sm">
        This series is archived and read-only.
      </p>
    );
  if (status === "active")
    return (
      <p className="border-warning/30 bg-warning/10 text-warning rounded-card border px-4 py-3 text-sm">
        This series is active. Changes must remain activation-ready and are
        blocked while an active campaign uses it.
      </p>
    );
  return null;
}

function SeriesEditorLoading(): React.JSX.Element {
  return (
    <div
      className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_400px]"
      aria-label="Loading content series"
    >
      <div className="space-y-6">
        <div className="border-border bg-surface rounded-card h-96 animate-pulse border" />
        <div className="border-border bg-surface rounded-card h-64 animate-pulse border" />
      </div>
      <div className="border-border bg-surface h-[540px] animate-pulse rounded-[2rem] border" />
    </div>
  );
}
