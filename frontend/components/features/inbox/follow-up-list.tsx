import { ChevronLeft, ChevronRight } from "lucide-react";

import { DateTime } from "@/components/shared/date-time";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import type {
  FollowUpListItem,
  PendingPage,
} from "@/lib/api/pending-contracts";
import { cn } from "@/lib/utils/class-names";

interface FollowUpListProps {
  data?: PendingPage<FollowUpListItem>;
  selectedId: string | null;
  isLoading: boolean;
  error?: string;
  page: number;
  onSelect: (id: string) => void;
  onPageChange: (page: number) => void;
  onRetry: () => void;
}

/** Coordinator work queue with compact donor and reply context. */
export function FollowUpList(props: FollowUpListProps): React.JSX.Element {
  if (props.isLoading) return <FollowUpListSkeleton />;
  if (props.error) {
    return <ErrorState description={props.error} onRetry={props.onRetry} />;
  }
  if (!props.data?.items.length) {
    return (
      <EmptyState
        title="No follow-ups"
        description="No items match the current queue filters."
      />
    );
  }

  const pageCount = Math.max(
    1,
    Math.ceil(props.data.total / props.data.page_size),
  );
  return (
    <section className="border-border bg-surface rounded-card overflow-hidden border">
      <ul className="divide-border divide-y">
        {props.data.items.map((item, index) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => props.onSelect(item.id)}
              className={cn(
                "focus-visible:outline-ring focus-visible:outline-inset w-full p-4 text-left focus-visible:outline-2",
                item.id === props.selectedId && "bg-primary-soft",
                index === 0 && item.status === "open" && "border-primary/30",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-medium">{item.donor.name}</p>
                  <p className="text-muted-foreground mt-0.5 truncate text-xs">
                    {item.campaign.name}
                  </p>
                </div>
                <DateTime value={item.updated_at} relative />
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <StatusBadge status={item.type} />
                <StatusBadge status={item.priority} />
                <span className="text-muted-foreground text-xs">
                  {item.assigned_to?.full_name ?? "Unassigned"}
                </span>
              </div>
              <p className="text-muted-foreground mt-3 line-clamp-2 text-sm">
                {item.latest_reply?.body ?? "No donor reply recorded."}
              </p>
            </button>
          </li>
        ))}
      </ul>
      <footer className="border-border flex items-center justify-between border-t px-4 py-3">
        <span className="text-muted-foreground text-xs">
          Page {props.page} of {pageCount}
        </span>
        <div className="flex gap-2">
          <Button
            type="button"
            size="icon"
            variant="secondary"
            aria-label="Previous page"
            disabled={props.page <= 1}
            onClick={() => props.onPageChange(props.page - 1)}
          >
            <ChevronLeft aria-hidden="true" />
          </Button>
          <Button
            type="button"
            size="icon"
            variant="secondary"
            aria-label="Next page"
            disabled={props.page >= pageCount}
            onClick={() => props.onPageChange(props.page + 1)}
          >
            <ChevronRight aria-hidden="true" />
          </Button>
        </div>
      </footer>
    </section>
  );
}

function FollowUpListSkeleton(): React.JSX.Element {
  return (
    <div aria-label="Loading follow-ups" className="space-y-2">
      {Array.from({ length: 6 }, (_, index) => (
        <div
          key={index}
          className="bg-surface-muted h-32 animate-pulse rounded"
        />
      ))}
    </div>
  );
}
