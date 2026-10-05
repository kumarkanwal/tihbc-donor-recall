"use client";

import { useMemo, useState } from "react";

import { DataTable } from "@/components/shared/data-table";
import { createDataTableColumnHelper } from "@/components/shared/data-table-types";
import { KpiCard } from "@/components/shared/kpi-card";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { useInactiveNumbers } from "@/hooks/use-metrics";
import {
  isPendingBackendUpdate,
  type InactiveNumberRow,
  type MetricsFilters,
} from "@/lib/api/pending-contracts";

interface InactiveNumbersReportProps {
  filters: MetricsFilters;
}

const columnHelper = createDataTableColumnHelper<InactiveNumberRow>();

/** Invalid and undeliverable donor number report with summary totals. */
export function InactiveNumbersReport({
  filters,
}: InactiveNumbersReportProps): React.JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const query = useInactiveNumbers({ ...filters, page, page_size: pageSize });
  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor("donor_name", {
          header: "Donor",
          enableSorting: false,
          cell: ({ getValue }) => (
            <span className="font-medium">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("phone", {
          header: "Phone",
          enableSorting: false,
        }),
        columnHelper.accessor("kind", {
          header: "Type",
          enableSorting: false,
          cell: ({ getValue }) => (
            <StatusBadge
              status={
                getValue() === "invalid" ? "invalid_number" : "undeliverable"
              }
            />
          ),
        }),
        columnHelper.accessor("reason", {
          header: "Reason",
          enableSorting: false,
        }),
        columnHelper.accessor("batch_name", {
          header: "Batch",
          enableSorting: false,
        }),
        columnHelper.accessor("campaign_name", {
          header: "Campaign",
          enableSorting: false,
          cell: ({ getValue }) => getValue() ?? "—",
        }),
        columnHelper.accessor("occurred_at", {
          header: "Occurred",
          enableSorting: false,
          cell: ({ getValue }) =>
            new Intl.DateTimeFormat("en-GB", {
              timeZone: "Asia/Karachi",
              day: "2-digit",
              month: "short",
              year: "numeric",
            }).format(new Date(getValue())),
        }),
      ]),
    [],
  );

  if (isPendingBackendUpdate(query.error)) {
    return (
      <EmptyState
        title="Available after backend update"
        description="Inactive-number reports will be connected after backend Task 2.11."
      />
    );
  }

  return (
    <div className="space-y-6" role="tabpanel">
      <section className="grid gap-4 sm:grid-cols-3">
        <KpiCard
          label="Invalid numbers"
          value={query.data?.summary.invalid ?? 0}
        />
        <KpiCard
          label="Undeliverable"
          value={query.data?.summary.undeliverable ?? 0}
        />
        <KpiCard
          label="Total inactive"
          value={query.data?.summary.total ?? 0}
        />
      </section>
      <DataTable
        columns={columns}
        data={query.data}
        showToolbar={false}
        isLoading={query.isPending}
        error={
          query.error
            ? "The inactive-number report could not be loaded."
            : undefined
        }
        onRetry={() => void query.refetch()}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value);
          setPage(1);
        }}
        emptyTitle="No inactive numbers"
        emptyDescription="Invalid and undeliverable donor numbers will appear here."
      />
    </div>
  );
}
