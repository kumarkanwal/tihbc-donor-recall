"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/shared/page-header";
import type { SortingState } from "@/components/shared/data-table-types";
import { Button } from "@/components/ui/button";
import { useCan } from "@/hooks/use-can";
import {
  getCampaignErrorMessage,
  useCampaignCatalog,
  type Campaign,
  type CampaignPage,
} from "@/hooks/use-campaigns";

import { CampaignListTable } from "./campaign-list-table";
import {
  CampaignStatusTabs,
  type CampaignStatusFilter,
} from "./campaign-status-tabs";

const defaultSorting: SortingState = [{ id: "start_at", desc: true }];

function shapePage(
  source: CampaignPage | undefined,
  search: string,
  sorting: SortingState,
  page: number,
  pageSize: number,
): CampaignPage | undefined {
  if (!source) return undefined;
  const term = search.trim().toLocaleLowerCase();
  const items = source.items.filter((campaign) =>
    [campaign.name, campaign.batch.name, campaign.primary_series.name].some(
      (value) => value.toLocaleLowerCase().includes(term),
    ),
  );
  const sort = sorting[0];
  if (sort) {
    items.sort((left, right) => compareCampaigns(left, right, sort.id));
    if (sort.desc) items.reverse();
  }
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    page_size: pageSize,
  };
}

function compareCampaigns(
  left: Campaign,
  right: Campaign,
  key: string,
): number {
  if (key === "enrollment_count" || key === "response_rate") {
    return left[key] - right[key];
  }
  const leftValue =
    key === "status" || key === "name" || key === "start_at" ? left[key] : "";
  const rightValue =
    key === "status" || key === "name" || key === "start_at" ? right[key] : "";
  return String(leftValue).localeCompare(String(rightValue), undefined, {
    numeric: true,
  });
}

/** Searchable, filterable campaign library. */
export function CampaignListScreen(): React.JSX.Element {
  const router = useRouter();
  const canManage = useCan(["admin"]);
  const [status, setStatus] = useState<CampaignStatusFilter>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const query = useCampaignCatalog(status === "all" ? undefined : status);
  const data = useMemo(
    () => shapePage(query.data, search, sorting, page, pageSize),
    [page, pageSize, query.data, search, sorting],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Campaigns"
        description="Schedule and monitor donor recall campaigns."
        actions={
          canManage ? (
            <Button asChild>
              <Link href="/campaigns/new">
                <Plus aria-hidden="true" />
                New campaign
              </Link>
            </Button>
          ) : undefined
        }
      />
      <CampaignStatusTabs
        value={status}
        onChange={(value) => {
          setStatus(value);
          setPage(1);
        }}
      />
      <CampaignListTable
        data={data}
        sorting={sorting}
        isPending={query.isPending}
        error={
          query.error
            ? getCampaignErrorMessage(
                query.error,
                "The campaigns could not be loaded.",
              )
            : undefined
        }
        onSortingChange={(value) => {
          setSorting(value);
          setPage(1);
        }}
        onSearchChange={(value) => {
          setSearch(value);
          setPage(1);
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value);
          setPage(1);
        }}
        onOpen={(campaign) => router.push(`/campaigns/${campaign.id}`)}
        onRetry={() => void query.refetch()}
      />
    </div>
  );
}
