"use client";

import { useMemo, useState } from "react";

import { DonorFilters } from "@/components/features/batches/batch-detail-parts";
import { DataTable } from "@/components/shared/data-table";
import {
  createDataTableColumnHelper,
  type SortingState,
} from "@/components/shared/data-table-types";
import { MaskedPhone } from "@/components/shared/masked-phone";
import {
  getDonorBatchErrorMessage,
  useBatchDonors,
  type Donor,
  type DonorListParameters,
} from "@/hooks/use-donor-batches";

const columnHelper = createDataTableColumnHelper<Donor>();
const defaultSorting: SortingState = [{ id: "full_name", desc: false }];

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function getDonorSort(sorting: SortingState): DonorListParameters["sort"] {
  const first = sorting[0];
  if (!first || (first.id !== "full_name" && first.id !== "created_at")) {
    return "full_name";
  }
  return `${first.desc ? "-" : ""}${first.id}` as DonorListParameters["sort"];
}

function useDonorColumns() {
  return useMemo(
    () =>
      columnHelper.columns([
        columnHelper.accessor("full_name", {
          header: "Name",
          cell: ({ getValue }) => (
            <span className="font-medium">{getValue()}</span>
          ),
        }),
        columnHelper.accessor("phone_e164", {
          header: "Phone",
          enableSorting: false,
          cell: ({ getValue }) => <MaskedPhone value={getValue()} />,
        }),
        columnHelper.accessor("segment", {
          header: "Segment",
          enableSorting: false,
          cell: ({ getValue }) => (
            <span className="capitalize">
              {getValue().replaceAll("_", " ")}
            </span>
          ),
        }),
        columnHelper.accessor("language", {
          header: "Language",
          enableSorting: false,
          cell: ({ getValue }) => (getValue() === "en" ? "English" : "Urdu"),
        }),
        columnHelper.accessor("city", {
          header: "City",
          enableSorting: false,
          cell: ({ getValue }) => getValue() || "—",
        }),
        columnHelper.accessor("blood_group", {
          header: "Blood group",
          enableSorting: false,
          cell: ({ getValue }) => getValue() || "—",
        }),
        columnHelper.accessor("last_donation_date", {
          header: "Last donation",
          enableSorting: false,
          cell: ({ getValue }) => formatDate(getValue()),
        }),
      ]),
    [],
  );
}

/** Filtered donor browser for one imported batch. */
export function BatchDonorsPanel({
  batchId,
  segments,
}: {
  batchId: string;
  segments: string[];
}): React.JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("");
  const [language, setLanguage] = useState<"" | "en" | "ur">("");
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const parameters = useMemo<DonorListParameters>(
    () => ({
      page,
      page_size: pageSize,
      search: search || undefined,
      segment: segment || undefined,
      language: language || undefined,
      sort: getDonorSort(sorting),
    }),
    [language, page, pageSize, search, segment, sorting],
  );
  const donors = useBatchDonors(batchId, parameters);
  const columns = useDonorColumns();
  const resetPage = () => setPage(1);

  return (
    <DataTable
      columns={columns}
      data={donors.data}
      sorting={sorting}
      onSortingChange={(value) => {
        setSorting(value);
        resetPage();
      }}
      onSearchChange={(value) => {
        setSearch(value.trim());
        resetPage();
      }}
      searchPlaceholder="Search donors by name or phone"
      filterSlot={
        <DonorFilters
          segments={segments}
          segment={segment}
          language={language}
          onSegmentChange={(value) => {
            setSegment(value);
            resetPage();
          }}
          onLanguageChange={(value) => {
            setLanguage(value);
            resetPage();
          }}
        />
      }
      onPageChange={setPage}
      onPageSizeChange={(value) => {
        setPageSize(value);
        resetPage();
      }}
      isLoading={donors.isPending}
      error={
        donors.error
          ? getDonorBatchErrorMessage(
              donors.error,
              "The donors could not be loaded.",
            )
          : undefined
      }
      onRetry={() => void donors.refetch()}
      emptyTitle="No donors found"
      emptyDescription="Try adjusting the donor search or filters."
    />
  );
}
