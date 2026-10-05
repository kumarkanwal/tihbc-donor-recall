"use client";

import { useMemo } from "react";

import { DataTable } from "@/components/shared/data-table";
import {
  createDataTableColumnHelper,
  type SortingState,
} from "@/components/shared/data-table-types";
import { DateTime } from "@/components/shared/date-time";
import { StatusBadge } from "@/components/shared/status-badge";
import type { Campaign, CampaignPage } from "@/hooks/use-campaigns";

import { CampaignProgress } from "./campaign-progress";

const columnHelper = createDataTableColumnHelper<Campaign>();

function useCampaignColumns() {
  return useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor("name", {
          header: "Name",
          cell: ({ getValue }) => (
            <span className="font-medium">{getValue()}</span>
          ),
        }),
        columnHelper.display({
          id: "batch",
          header: "Batch",
          cell: ({ row }) => row.original.batch.name,
        }),
        columnHelper.display({
          id: "primary_series",
          header: "Primary series",
          cell: ({ row }) => row.original.primary_series.name,
        }),
        columnHelper.accessor("status", {
          header: "Status",
          cell: ({ getValue }) => <StatusBadge status={getValue()} />,
        }),
        columnHelper.accessor("start_at", {
          header: "Start date",
          cell: ({ getValue }) => <DateTime value={getValue()} />,
        }),
        columnHelper.accessor("enrollment_count", {
          header: "Enrolled",
          cell: ({ getValue }) => (
            <span className="tabular-nums">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("response_rate", {
          header: "Response rate",
          cell: ({ getValue }) => (
            <span className="tabular-nums">{getValue().toFixed(1)}%</span>
          ),
        }),
        columnHelper.display({
          id: "progress",
          header: "Progress",
          cell: ({ row }) => (
            <CampaignProgress
              responded={row.original.responded_count}
              enrolled={row.original.enrollment_count}
            />
          ),
        }),
      ]),
    [],
  );
}

interface CampaignListTableProps {
  data?: CampaignPage;
  sorting: SortingState;
  isPending: boolean;
  error?: string;
  onSortingChange: (sorting: SortingState) => void;
  onSearchChange: (search: string) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onOpen: (campaign: Campaign) => void;
  onRetry: () => void;
}

/** Campaign index table using the shared loading/error/empty states. */
export function CampaignListTable(
  props: CampaignListTableProps,
): React.JSX.Element {
  const columns = useCampaignColumns();
  return (
    <DataTable
      columns={columns}
      data={props.data}
      sorting={props.sorting}
      onSortingChange={props.onSortingChange}
      onSearchChange={props.onSearchChange}
      searchPlaceholder="Search campaigns"
      onPageChange={props.onPageChange}
      onPageSizeChange={props.onPageSizeChange}
      onRowClick={props.onOpen}
      isLoading={props.isPending}
      error={props.error}
      onRetry={props.onRetry}
      emptyTitle="No campaigns"
      emptyDescription="Create a campaign to assign a donor batch to recall sequences."
    />
  );
}
