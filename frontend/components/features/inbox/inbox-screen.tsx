"use client";

import { Download } from "lucide-react";
import { useDeferredValue, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { useCampaignCatalog } from "@/hooks/use-campaigns";
import {
  isPendingBackendUpdate,
  useExportFollowUps,
  useFollowUps,
  useFollowUpSummary,
} from "@/hooks/use-follow-ups";
import type {
  FollowUpFilters,
  FollowUpStatus,
} from "@/lib/api/pending-contracts";

import { FollowUpDetailPanel } from "./follow-up-detail-panel";
import { FollowUpList } from "./follow-up-list";
import { InboxFilters, type InboxTypeFilter } from "./inbox-filters";

/** Live coordinator queue with filters, detail context, and workflow actions. */
export function InboxScreen(): React.JSX.Element {
  const [type, setType] = useState<InboxTypeFilter>("needs_call");
  const [status, setStatus] = useState<FollowUpStatus>("open");
  const [assignedToMe, setAssignedToMe] = useState(false);
  const [campaignId, setCampaignId] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const deferredSearch = useDeferredValue(search.trim());
  const filters: FollowUpFilters = {
    type: type === "all" ? undefined : type,
    status,
    assigned_to: assignedToMe ? "me" : undefined,
    campaign_id: campaignId || undefined,
    search: deferredSearch || undefined,
    page,
    page_size: 20,
  };
  const summaryFilters: FollowUpFilters = {
    assigned_to: filters.assigned_to,
    campaign_id: filters.campaign_id,
    search: filters.search,
  };
  const query = useFollowUps(filters);
  const summary = useFollowUpSummary(summaryFilters);
  const campaigns = useCampaignCatalog(undefined);
  const exportMutation = useExportFollowUps(filters);
  const unavailable = isPendingBackendUpdate(query.error);

  function resetPage(): void {
    setPage(1);
    setSelectedId(null);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Follow-up Inbox"
        description="Review donor responses and complete coordinator follow-up work."
        actions={
          <Button
            type="button"
            variant="secondary"
            disabled={unavailable || exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            <Download aria-hidden="true" />
            Export CSV
          </Button>
        }
      />
      {unavailable ? (
        <EmptyState
          title="Available after backend update"
          description="The follow-up inbox API will be connected after backend Task 2.10."
        />
      ) : (
        <>
          <InboxFilters
            type={type}
            status={status}
            assignedToMe={assignedToMe}
            campaignId={campaignId}
            search={search}
            summary={summary.data}
            campaigns={
              campaigns.data?.items.map(({ id, name }) => ({ id, name })) ?? []
            }
            onTypeChange={(value) => {
              setType(value);
              resetPage();
            }}
            onStatusChange={(value) => {
              setStatus(value);
              resetPage();
            }}
            onAssignedChange={(value) => {
              setAssignedToMe(value);
              resetPage();
            }}
            onCampaignChange={(value) => {
              setCampaignId(value);
              resetPage();
            }}
            onSearchChange={(value) => {
              setSearch(value);
              resetPage();
            }}
          />
          <div className="grid items-start gap-6 xl:grid-cols-[minmax(22rem,0.9fr)_minmax(28rem,1.1fr)]">
            <FollowUpList
              data={query.data}
              selectedId={selectedId}
              isLoading={query.isPending}
              error={
                query.error
                  ? "The follow-up queue could not be loaded."
                  : undefined
              }
              page={page}
              onSelect={setSelectedId}
              onPageChange={(value) => {
                setPage(value);
                setSelectedId(null);
              }}
              onRetry={() => void query.refetch()}
            />
            <FollowUpDetailPanel selectedId={selectedId} />
          </div>
          {exportMutation.error ? (
            <p role="alert" className="text-danger text-sm">
              The follow-up export could not be created.
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}
