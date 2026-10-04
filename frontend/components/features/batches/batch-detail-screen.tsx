"use client";

import * as Tabs from "@radix-ui/react-tabs";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BatchBreakdowns } from "@/components/features/batches/batch-breakdowns";
import {
  BatchTabTrigger,
  DetailLoading,
  DonorFilters,
  type DetailTab,
} from "@/components/features/batches/batch-detail-parts";
import { ValidationIssuesTable } from "@/components/features/batches/validation-issues-table";
import { DataTable } from "@/components/shared/data-table";
import {
  createDataTableColumnHelper,
  type SortingState,
} from "@/components/shared/data-table-types";
import { ErrorState } from "@/components/shared/error-state";
import { KpiCard } from "@/components/shared/kpi-card";
import { MaskedPhone } from "@/components/shared/masked-phone";
import { PageHeader } from "@/components/shared/page-header";
import {
  getDonorBatchErrorMessage,
  useBatchDonors,
  useBatchValidationReport,
  useDonorBatch,
  type Donor,
  type DonorListParameters,
} from "@/hooks/use-donor-batches";

const columnHelper = createDataTableColumnHelper<Donor>();
const defaultSorting: SortingState = [{ id: "full_name", desc: false }];

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

function getDonorSort(sorting: SortingState): DonorListParameters["sort"] {
  const first = sorting[0];
  if (!first || (first.id !== "full_name" && first.id !== "created_at")) {
    return "full_name";
  }
  return `${first.desc ? "-" : ""}${first.id}` as DonorListParameters["sort"];
}

/** Donor batch summary, donor browser, and persisted validation report. */
export function BatchDetailScreen({
  batchId,
}: {
  batchId: string;
}): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<DetailTab>("donors");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("");
  const [language, setLanguage] = useState<"" | "en" | "ur">("");
  const [sorting, setSorting] = useState<SortingState>(defaultSorting);
  const batch = useDonorBatch(batchId);
  const donorParameters = useMemo<DonorListParameters>(
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
  const donors = useBatchDonors(batchId, donorParameters);
  const validation = useBatchValidationReport(
    batchId,
    activeTab === "validation",
  );
  const columns = useMemo(
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

  if (batch.isPending) {
    return <DetailLoading />;
  }
  if (batch.error || !batch.data) {
    return (
      <ErrorState
        title="Could not load batch"
        description={getDonorBatchErrorMessage(
          batch.error,
          "The donor batch could not be loaded.",
        )}
        onRetry={() => void batch.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={batch.data.name}
        description={`Uploaded from ${batch.data.original_filename}`}
        breadcrumb={<Link href="/batches">Donor Batches</Link>}
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total rows" value={batch.data.total_rows} />
        <KpiCard label="Valid donors" value={batch.data.valid_rows} />
        <KpiCard label="Invalid rows" value={batch.data.invalid_rows} />
        <KpiCard label="Campaigns" value={batch.data.campaign_count} />
      </div>
      <BatchBreakdowns {...batch.data} />

      <Tabs.Root
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as DetailTab)}
      >
        <Tabs.List
          aria-label="Batch details"
          className="border-border flex gap-1 border-b"
        >
          <BatchTabTrigger value="donors">Donors</BatchTabTrigger>
          <BatchTabTrigger value="validation">
            Validation report
          </BatchTabTrigger>
        </Tabs.List>
        <Tabs.Content
          value="donors"
          className="mt-5 focus-visible:outline-none"
        >
          <DataTable
            columns={columns}
            data={donors.data}
            sorting={sorting}
            onSortingChange={(nextSorting) => {
              setSorting(nextSorting);
              setPage(1);
            }}
            onSearchChange={(nextSearch) => {
              setSearch(nextSearch.trim());
              setPage(1);
            }}
            searchPlaceholder="Search donors by name or phone"
            filterSlot={
              <DonorFilters
                segments={batch.data.segment_breakdown.map(
                  ({ segment: key }) => key,
                )}
                segment={segment}
                language={language}
                onSegmentChange={(value) => {
                  setSegment(value);
                  setPage(1);
                }}
                onLanguageChange={(value) => {
                  setLanguage(value);
                  setPage(1);
                }}
              />
            }
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
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
        </Tabs.Content>
        <Tabs.Content
          value="validation"
          className="mt-5 focus-visible:outline-none"
        >
          {validation.isPending ? (
            <div
              className="border-border bg-surface rounded-card h-40 animate-pulse border"
              aria-label="Loading validation report"
            />
          ) : validation.error ? (
            <ErrorState
              description={getDonorBatchErrorMessage(
                validation.error,
                "The validation report could not be loaded.",
              )}
              onRetry={() => void validation.refetch()}
            />
          ) : (
            <ValidationIssuesTable issues={validation.data ?? []} />
          )}
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
