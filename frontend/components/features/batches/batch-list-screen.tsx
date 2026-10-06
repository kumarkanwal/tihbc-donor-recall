"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable } from "@/components/shared/data-table";
import {
  createDataTableColumnHelper,
  type SortingState,
} from "@/components/shared/data-table-types";
import { DateTime } from "@/components/shared/date-time";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { useCan } from "@/hooks/use-can";
import {
  getDonorBatchErrorMessage,
  useDonorBatches,
  type BatchListParameters,
  type DonorBatch,
} from "@/hooks/use-donor-batches";

const columnHelper = createDataTableColumnHelper<DonorBatch>();
const defaultSorting: SortingState = [{ id: "created_at", desc: true }];

function getSortParameter(sorting: SortingState): BatchListParameters["sort"] {
  const first = sorting[0];
  if (!first || (first.id !== "name" && first.id !== "created_at")) {
    return "-created_at";
  }
  return `${first.desc ? "-" : ""}${first.id}` as BatchListParameters["sort"];
}

/** Searchable, server-sorted donor batch index. */
export function BatchListScreen(): React.JSX.Element {
  const router = useRouter();
  const canUpload = useCan(["admin"]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const parameters = useMemo<BatchListParameters>(
    () => ({
      page,
      page_size: pageSize,
      search: search || undefined,
      sort: getSortParameter(sorting),
    }),
    [page, pageSize, search, sorting],
  );
  const batches = useDonorBatches(parameters);
  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor("name", {
          header: "Name",
          cell: ({ getValue }) => (
            <span className="font-medium">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("original_filename", {
          header: "File name",
          enableSorting: false,
        }),
        columnHelper.display({
          id: "rows",
          header: "Valid / total rows",
          cell: ({ row }) => (
            <span className="tabular-nums">
              {row.original.valid_rows} / {row.original.total_rows}
            </span>
          ),
        }),
        columnHelper.accessor("invalid_rows", {
          header: "Invalid rows",
          enableSorting: false,
          cell: ({ getValue }) => (
            <span className="tabular-nums">{getValue()}</span>
          ),
        }),
        columnHelper.display({
          id: "uploaded_by",
          header: "Uploaded by",
          cell: ({ row }) => row.original.uploaded_by.full_name,
        }),
        columnHelper.accessor("created_at", {
          header: "Uploaded at",
          cell: ({ getValue }) => <DateTime value={getValue()} />,
        }),
        columnHelper.accessor("campaign_count", {
          header: "Used in campaigns",
          enableSorting: false,
          cell: ({ getValue }) => (
            <span className="tabular-nums">{getValue()}</span>
          ),
        }),
      ]),
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Donor Batches"
        description="Upload, validate, and review donor lists before launching campaigns."
        actions={
          canUpload ? (
            <Button asChild>
              <Link href="/batches/new" data-testid="upload-batch-action">
                <Plus aria-hidden="true" />
                Upload batch
              </Link>
            </Button>
          ) : undefined
        }
      />
      <DataTable
        columns={columns}
        data={batches.data}
        sorting={sorting}
        onSortingChange={(nextSorting) => {
          setSorting(nextSorting);
          setPage(1);
        }}
        onSearchChange={(nextSearch) => {
          setSearch(nextSearch.trim());
          setPage(1);
        }}
        searchPlaceholder="Search batches by name"
        onPageChange={setPage}
        onPageSizeChange={(nextPageSize) => {
          setPageSize(nextPageSize);
          setPage(1);
        }}
        onRowClick={(batch) => router.push(`/batches/${batch.id}`)}
        isLoading={batches.isPending}
        error={
          batches.error
            ? getDonorBatchErrorMessage(
                batches.error,
                "The donor batches could not be loaded.",
              )
            : undefined
        }
        onRetry={() => void batches.refetch()}
        emptyTitle="No donor batches"
        emptyDescription={
          canUpload
            ? "Upload a CSV or XLSX file to add your first donor batch."
            : "No donor batches have been uploaded yet."
        }
      />
    </div>
  );
}
