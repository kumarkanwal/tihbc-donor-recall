"use client";

import { useMemo, useState } from "react";

import { DataTable } from "@/components/shared/data-table";
import { createDataTableColumnHelper } from "@/components/shared/data-table-types";
import { StatusBadge } from "@/components/shared/status-badge";
import { useStaffUsers, type StaffUser } from "@/hooks/use-settings";

const columnHelper = createDataTableColumnHelper<StaffUser>();

/** Read-only paginated staff directory. */
export function UsersSettings(): React.JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const query = useStaffUsers(page, pageSize);
  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor("full_name", {
          header: "Name",
          enableSorting: false,
          cell: ({ getValue }) => (
            <span className="font-medium">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("email", {
          header: "Email",
          enableSorting: false,
        }),
        columnHelper.accessor("role", {
          header: "Role",
          enableSorting: false,
          cell: ({ getValue }) => (
            <StatusBadge status={getValue()} label={getValue()} />
          ),
        }),
      ]),
    [],
  );

  return (
    <DataTable
      columns={columns}
      data={query.data}
      showToolbar={false}
      isLoading={query.isPending}
      error={query.error ? "The user list could not be loaded." : undefined}
      onRetry={() => void query.refetch()}
      onPageChange={setPage}
      onPageSizeChange={(value) => {
        setPageSize(value);
        setPage(1);
      }}
      emptyTitle="No active users"
      emptyDescription="Active staff accounts will appear here."
    />
  );
}
