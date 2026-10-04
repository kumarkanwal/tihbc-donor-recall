"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { SeriesGrid } from "@/components/features/series/series-library-grid";
import {
  SeriesTable,
  sortSeriesPage,
} from "@/components/features/series/series-library-table";
import {
  SeriesLibraryToolbar,
  type SeriesFilters,
} from "@/components/features/series/series-library-toolbar";
import type { SortingState } from "@/components/shared/data-table-types";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { useCan } from "@/hooks/use-can";
import {
  useContentSeries,
  type SeriesListParameters,
} from "@/hooks/use-content-series";

const initialFilters: SeriesFilters = {
  kind: "",
  status: "",
  tag: "",
  language: "",
};

/** Searchable table/grid content-series library. */
export function SeriesLibraryScreen(): React.JSX.Element {
  const router = useRouter();
  const canManage = useCan(["admin"]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(initialFilters);
  const [view, setView] = useState<"table" | "grid">("table");
  const [sorting, setSorting] = useState<SortingState>([
    { id: "name", desc: false },
  ]);
  const parameters = useMemo<SeriesListParameters>(
    () => ({
      page,
      page_size: pageSize,
      search: search || undefined,
      kind: filters.kind || undefined,
      status: filters.status || undefined,
      tag: filters.tag.trim() || undefined,
      language: filters.language || undefined,
    }),
    [filters, page, pageSize, search],
  );
  const query = useContentSeries(parameters);
  const sortedData = useMemo(
    () => sortSeriesPage(query.data, sorting),
    [query.data, sorting],
  );
  const updatePageSize = (value: number) => {
    setPageSize(value);
    setPage(1);
  };
  const resultProps = {
    isPending: query.isPending,
    error: query.error,
    canManage,
    onRetry: () => void query.refetch(),
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Content Series"
        description="Manage bilingual recall message sequences."
        actions={
          canManage ? (
            <Button asChild>
              <Link href="/series/new">
                <Plus aria-hidden="true" />
                New series
              </Link>
            </Button>
          ) : undefined
        }
      />
      <SeriesLibraryToolbar
        filters={filters}
        view={view}
        onFiltersChange={(next) => {
          setFilters(next);
          setPage(1);
        }}
        onSearchChange={(value) => {
          setSearch(value);
          setPage(1);
        }}
        onViewChange={setView}
      />
      {view === "table" ? (
        <SeriesTable
          {...resultProps}
          data={sortedData}
          sorting={sorting}
          onSortingChange={setSorting}
          onPageChange={setPage}
          onPageSizeChange={updatePageSize}
          onOpen={(series) => router.push(`/series/${series.id}`)}
        />
      ) : (
        <SeriesGrid
          {...resultProps}
          data={query.data}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={updatePageSize}
        />
      )}
    </div>
  );
}
