"use client";

import * as Tabs from "@radix-ui/react-tabs";
import Link from "next/link";
import { useState } from "react";

import { BatchBreakdowns } from "@/components/features/batches/batch-breakdowns";
import { BatchDonorsPanel } from "@/components/features/batches/batch-donors-panel";
import {
  BatchTabTrigger,
  DetailLoading,
  type DetailTab,
} from "@/components/features/batches/batch-detail-parts";
import { ValidationIssuesTable } from "@/components/features/batches/validation-issues-table";
import { ErrorState } from "@/components/shared/error-state";
import { KpiCard } from "@/components/shared/kpi-card";
import { PageHeader } from "@/components/shared/page-header";
import {
  getDonorBatchErrorMessage,
  useBatchValidationReport,
  useDonorBatch,
} from "@/hooks/use-donor-batches";

/** Donor batch summary, donor browser, and persisted validation report. */
export function BatchDetailScreen({
  batchId,
}: {
  batchId: string;
}): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<DetailTab>("donors");
  const batch = useDonorBatch(batchId);
  const validation = useBatchValidationReport(
    batchId,
    activeTab === "validation",
  );

  if (batch.isPending) {
    return <DetailLoading />;
  }
  if (batch.error || !batch.data) {
    return (
      <ErrorState
        title="Could not load batch"
        description={getDonorBatchErrorMessage(
          batch.error,
          "The donor batch could not be loaded.",
        )}
        onRetry={() => void batch.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={batch.data.name}
        description={`Uploaded from ${batch.data.original_filename}`}
        breadcrumb={<Link href="/batches">Donor Batches</Link>}
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total rows" value={batch.data.total_rows} />
        <KpiCard label="Valid donors" value={batch.data.valid_rows} />
        <KpiCard label="Invalid rows" value={batch.data.invalid_rows} />
        <KpiCard label="Campaigns" value={batch.data.campaign_count} />
      </div>
      <BatchBreakdowns {...batch.data} />

      <Tabs.Root
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as DetailTab)}
      >
        <Tabs.List
          aria-label="Batch details"
          className="border-border flex gap-1 border-b"
        >
          <BatchTabTrigger value="donors">Donors</BatchTabTrigger>
          <BatchTabTrigger value="validation">
            Validation report
          </BatchTabTrigger>
        </Tabs.List>
        <Tabs.Content
          value="donors"
          className="mt-5 focus-visible:outline-none"
        >
          <BatchDonorsPanel
            batchId={batchId}
            segments={batch.data.segment_breakdown.map(
              ({ segment }) => segment,
            )}
          />
        </Tabs.Content>
        <Tabs.Content
          value="validation"
          className="mt-5 focus-visible:outline-none"
        >
          {validation.isPending ? (
            <div
              className="border-border bg-surface rounded-card h-40 animate-pulse border"
              aria-label="Loading validation report"
            />
          ) : validation.error ? (
            <ErrorState
              description={getDonorBatchErrorMessage(
                validation.error,
                "The validation report could not be loaded.",
              )}
              onRetry={() => void validation.refetch()}
            />
          ) : (
            <ValidationIssuesTable issues={validation.data ?? []} />
          )}
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
