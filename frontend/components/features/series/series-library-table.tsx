"use client";

import { useMemo } from "react";

import { SeriesActions } from "@/components/features/series/series-actions";
import { DataTable } from "@/components/shared/data-table";
import {
  createDataTableColumnHelper,
  type SortingState,
} from "@/components/shared/data-table-types";
import { StatusBadge } from "@/components/shared/status-badge";
import {
  getContentSeriesErrorMessage,
  type ContentSeries,
  type ContentSeriesPage,
} from "@/hooks/use-content-series";

const columnHelper = createDataTableColumnHelper<ContentSeries>();

function useSeriesColumns() {
  return useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor("name", {
          header: "Name",
          cell: ({ getValue }) => (
            <span className="font-medium">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("kind", {
          header: "Kind",
          cell: ({ getValue }) => (
            <StatusBadge
              status={getValue()}
              label={getValue() === "primary" ? "Primary" : "Secondary"}
            />
          ),
        }),
        columnHelper.accessor("status", {
          header: "Status",
          cell: ({ getValue }) => <StatusBadge status={getValue()} />,
        }),
        columnHelper.accessor("languages", {
          header: "Languages",
          enableSorting: false,
          cell: ({ getValue }) =>
            getValue()
              .map((value) => (value === "en" ? "English" : "Urdu"))
              .join(", "),
        }),
        columnHelper.accessor("step_count", {
          header: "Steps",
          cell: ({ getValue }) => (
            <span className="tabular-nums">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("tags", {
          header: "Tags",
          enableSorting: false,
          cell: ({ getValue }) => getValue().join(", ") || "—",
        }),
        columnHelper.display({
          id: "actions",
          header: "Actions",
          cell: ({ row }) => <SeriesActions series={row.original} compact />,
        }),
      ]),
    [],
  );
}

export function sortSeriesPage(
  data: ContentSeriesPage | undefined,
  sorting: SortingState,
): ContentSeriesPage | undefined {
  if (!data || !sorting[0]) return data;
  const { id, desc } = sorting[0];
  const items = [...data.items].sort((left, right) =>
    String(left[id as keyof ContentSeries]).localeCompare(
      String(right[id as keyof ContentSeries]),
      undefined,
      { numeric: true },
    ),
  );
  if (desc) items.reverse();
  return { ...data, items };
}

interface SeriesTableProps {
  data?: ContentSeriesPage;
  sorting: SortingState;
  isPending: boolean;
  error: unknown;
  canManage: boolean;
  onSortingChange: (sorting: SortingState) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onOpen: (series: ContentSeries) => void;
  onRetry: () => void;
}

/** Sortable table view for the content-series library. */
export function SeriesTable({
  data,
  sorting,
  isPending,
  error,
  canManage,
  onSortingChange,
  onPageChange,
  onPageSizeChange,
  onOpen,
  onRetry,
}: SeriesTableProps): React.JSX.Element {
  const columns = useSeriesColumns();
  return (
    <DataTable
      columns={columns}
      data={data}
      sorting={sorting}
      onSortingChange={onSortingChange}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
      onRowClick={onOpen}
      isLoading={isPending}
      error={
        error
          ? getContentSeriesErrorMessage(
              error,
              "The content series could not be loaded.",
            )
          : undefined
      }
      onRetry={onRetry}
      emptyTitle="No content series"
      emptyDescription={
        canManage
          ? "Create a series to start building recall messages."
          : "No content series are available yet."
      }
      showToolbar={false}
    />
  );
}
