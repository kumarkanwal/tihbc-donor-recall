"use client";

import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useMemo, type ReactNode } from "react";
import { useTable, type OnChangeFn, type RowData } from "@tanstack/react-table";

import { DataTablePagination } from "@/components/shared/data-table-pagination";
import { DataTableSkeleton } from "@/components/shared/data-table-skeleton";
import { DataTableToolbar } from "@/components/shared/data-table-toolbar";
import {
  dataTableFeatures,
  type DataTableColumn,
  type PaginatedData,
  type SortingState,
} from "@/components/shared/data-table-types";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { cn } from "@/lib/utils/class-names";

interface DataTableProps<TData extends RowData> {
  columns: DataTableColumn<TData>[];
  data?: PaginatedData<TData>;
  sorting?: SortingState;
  onSortingChange?: (sorting: SortingState) => void;
  onSearchChange?: (search: string) => void;
  searchPlaceholder?: string;
  filterSlot?: ReactNode;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  onRowClick?: (row: TData) => void;
  isLoading?: boolean;
  error?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  showToolbar?: boolean;
}

const emptySorting: SortingState = [];

/** Typed server-driven table with shared states and controls. */
export function DataTable<TData extends RowData>({
  columns,
  data,
  sorting = emptySorting,
  onSortingChange,
  onSearchChange,
  searchPlaceholder = "Search",
  filterSlot,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  isLoading = false,
  error,
  onRetry,
  emptyTitle = "No results",
  emptyDescription = "Try adjusting your search or filters.",
  showToolbar = true,
}: DataTableProps<TData>): React.JSX.Element {
  const rows = useMemo(() => data?.items ?? [], [data]);
  const page = data?.page ?? 1;
  const pageSize = data?.page_size ?? 20;
  const total = data?.total ?? 0;
  const handleSorting: OnChangeFn<SortingState> = (updater) => {
    const nextSorting =
      typeof updater === "function" ? updater(sorting) : updater;
    onSortingChange?.(nextSorting);
  };
  const table = useTable({
    features: dataTableFeatures,
    columns,
    data: rows,
    state: {
      sorting,
      pagination: { pageIndex: page - 1, pageSize },
    },
    onSortingChange: handleSorting,
    manualSorting: true,
    manualPagination: true,
    rowCount: total,
  });

  return (
    <section className="rounded-card border-border bg-surface shadow-surface overflow-hidden border">
      {showToolbar ? (
        <DataTableToolbar
          onSearchChange={onSearchChange}
          searchPlaceholder={searchPlaceholder}
          filterSlot={filterSlot}
        />
      ) : null}

      {error ? (
        <ErrorState
          description={error}
          onRetry={onRetry}
          className="rounded-none border-0"
        />
      ) : rows.length === 0 && !isLoading ? (
        <EmptyState
          title={emptyTitle}
          description={emptyDescription}
          className="rounded-none border-0"
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-max border-collapse text-left text-sm">
            <thead className="bg-surface-muted">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const sorted = header.column.getIsSorted();
                    const SortIcon =
                      sorted === "asc"
                        ? ArrowUp
                        : sorted === "desc"
                          ? ArrowDown
                          : ArrowUpDown;
                    return (
                      <th
                        key={header.id}
                        className="border-border border-b px-4 py-3 font-medium"
                      >
                        {header.isPlaceholder ? null : header.column.getCanSort() ? (
                          <button
                            type="button"
                            className="focus-visible:outline-ring inline-flex items-center gap-2 rounded focus-visible:outline-2 focus-visible:outline-offset-2"
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            <table.FlexRender header={header} />
                            <SortIcon
                              aria-hidden="true"
                              className="text-muted-foreground size-4"
                              strokeWidth={1.75}
                            />
                          </button>
                        ) : (
                          <table.FlexRender header={header} />
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody aria-busy={isLoading}>
              {isLoading ? (
                <DataTableSkeleton
                  columnCount={columns.length}
                  rowCount={pageSize}
                />
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    tabIndex={onRowClick ? 0 : undefined}
                    onClick={() => onRowClick?.(row.original)}
                    onKeyDown={(event) => {
                      if (
                        onRowClick &&
                        (event.key === "Enter" || event.key === " ")
                      ) {
                        event.preventDefault();
                        onRowClick(row.original);
                      }
                    }}
                    className={cn(
                      "hover:bg-surface-muted transition-colors",
                      onRowClick &&
                        "focus-visible:outline-inset focus-visible:outline-ring cursor-pointer focus-visible:outline-2",
                    )}
                  >
                    {row.getAllCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="border-border border-b px-4 py-3 last:border-b-0"
                      >
                        <table.FlexRender cell={cell} />
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {!error && !isLoading ? (
        <DataTablePagination
          page={page}
          pageSize={pageSize}
          total={total}
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
        />
      ) : null}
    </section>
  );
}
