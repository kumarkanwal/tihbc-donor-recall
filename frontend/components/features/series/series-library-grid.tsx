import { SeriesCard } from "@/components/features/series/series-card";
import { DataTablePagination } from "@/components/shared/data-table-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import {
  getContentSeriesErrorMessage,
  type ContentSeriesPage,
} from "@/hooks/use-content-series";

interface SeriesGridProps {
  data?: ContentSeriesPage;
  isPending: boolean;
  error: unknown;
  canManage: boolean;
  page: number;
  pageSize: number;
  onRetry: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

/** Paginated card view for the content-series library. */
export function SeriesGrid({
  data,
  isPending,
  error,
  canManage,
  page,
  pageSize,
  onRetry,
  onPageChange,
  onPageSizeChange,
}: SeriesGridProps): React.JSX.Element {
  if (isPending)
    return (
      <div
        className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
        aria-label="Loading content series"
      >
        {[0, 1, 2, 3, 4, 5].map((value) => (
          <div
            key={value}
            className="border-border bg-surface rounded-card h-64 animate-pulse border"
          />
        ))}
      </div>
    );
  if (error)
    return (
      <ErrorState
        description={getContentSeriesErrorMessage(
          error,
          "The content series could not be loaded.",
        )}
        onRetry={onRetry}
      />
    );
  if (!data?.items.length)
    return (
      <EmptyState
        title="No content series"
        description={
          canManage
            ? "Create a series to start building recall messages."
            : "No content series are available yet."
        }
      />
    );
  return (
    <section className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.items.map((series) => (
          <SeriesCard key={series.id} series={series} />
        ))}
      </div>
      <div className="border-border bg-surface rounded-card border">
        <DataTablePagination
          page={page}
          pageSize={pageSize}
          total={data.total}
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
        />
      </div>
    </section>
  );
}
