"use client";

import Link from "next/link";
import { useState } from "react";

import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { useCan } from "@/hooks/use-can";
import {
  getCampaignErrorMessage,
  useCampaign,
  useCampaignEnrollments,
  useUpdateCampaign,
  type CampaignCreate,
  type EnrollmentStatus,
} from "@/hooks/use-campaigns";

import { CampaignDetailActions } from "./campaign-detail-actions";
import { CampaignForm } from "./campaign-form";
import { CampaignReadonlySettings } from "./campaign-readonly-settings";
import { CampaignSequenceTimeline } from "./campaign-sequence-timeline";
import { EnrollmentDrawer } from "./enrollment-drawer";
import { EnrollmentStatusCards } from "./enrollment-status-cards";
import { EnrollmentTable } from "./enrollment-table";

/** Campaign lifecycle, sequence, and enrollment detail screen. */
export function CampaignDetailScreen({
  campaignId,
}: {
  campaignId: string;
}): React.JSX.Element {
  const canManage = useCan(["admin"]);
  const campaignQuery = useCampaign(campaignId);
  const updateCampaign = useUpdateCampaign(campaignId);
  const [status, setStatus] = useState<EnrollmentStatus>();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState<
    string | null
  >(null);
  const enrollments = useCampaignEnrollments(campaignId, {
    status,
    search: search || undefined,
    page,
    page_size: pageSize,
  });
  const campaign = campaignQuery.data;

  if (campaignQuery.isPending) return <CampaignDetailLoading />;
  if (campaignQuery.error || !campaign) {
    return (
      <ErrorState
        title="Could not load campaign"
        description={getCampaignErrorMessage(
          campaignQuery.error,
          "The campaign could not be loaded.",
        )}
        onRetry={() => void campaignQuery.refetch()}
      />
    );
  }

  async function save(input: CampaignCreate): Promise<void> {
    try {
      await updateCampaign.mutateAsync(input);
    } catch {
      /* Inline error. */
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={campaign.name}
        description={`${campaign.enrollment_count} enrolled · ${campaign.response_rate.toFixed(1)}% response rate`}
        breadcrumb={<Link href="/campaigns">Campaigns</Link>}
        actions={
          <div className="flex items-start gap-3">
            <StatusBadge status={campaign.status} />
            <CampaignDetailActions campaign={campaign} canManage={canManage} />
          </div>
        }
      />
      {!canManage ? (
        <p className="border-info/30 bg-info/10 text-info rounded-card border px-4 py-3 text-sm">
          Coordinator view: campaign settings and lifecycle actions are
          read-only.
        </p>
      ) : null}
      {campaign.status === "draft" ? (
        <CampaignForm
          campaign={campaign}
          readOnly={!canManage}
          pending={updateCampaign.isPending}
          error={updateCampaign.error}
          onSave={(input) => void save(input)}
        />
      ) : (
        <CampaignReadonlySettings campaign={campaign} />
      )}
      <EnrollmentStatusCards
        counts={campaign.enrollment_counts}
        selected={status}
        onSelect={(value) => {
          setStatus(value);
          setPage(1);
        }}
      />
      <CampaignSequenceTimeline
        primarySeriesId={campaign.primary_series.id}
        secondarySeriesId={campaign.secondary_series.id}
      />
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Enrollments</h2>
        <EnrollmentTable
          data={enrollments.data}
          isPending={enrollments.isPending}
          error={enrollments.error}
          onSearchChange={(value) => {
            setSearch(value);
            setPage(1);
          }}
          onPageChange={setPage}
          onPageSizeChange={(value) => {
            setPageSize(value);
            setPage(1);
          }}
          onDetails={setSelectedEnrollmentId}
          onRetry={() => void enrollments.refetch()}
        />
      </section>
      <EnrollmentDrawer
        enrollmentId={selectedEnrollmentId}
        onClose={() => setSelectedEnrollmentId(null)}
      />
    </div>
  );
}

function CampaignDetailLoading(): React.JSX.Element {
  return (
    <div aria-label="Loading campaign" className="space-y-6">
      <div className="bg-surface-muted h-20 animate-pulse rounded" />
      <div className="bg-surface-muted h-64 animate-pulse rounded" />
      <div className="bg-surface-muted h-80 animate-pulse rounded" />
    </div>
  );
}
