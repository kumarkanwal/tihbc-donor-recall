import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { useFollowUp } from "@/hooks/use-follow-ups";

import { FollowUpActions } from "./follow-up-actions";
import { FollowUpDetailContent } from "./follow-up-detail-content";

/** Selected follow-up detail and coordinator workflow panel. */
export function FollowUpDetailPanel({
  selectedId,
}: {
  selectedId: string | null;
}): React.JSX.Element {
  const query = useFollowUp(selectedId);
  if (!selectedId) {
    return (
      <EmptyState
        title="Select a follow-up"
        description="Choose an item from the queue to review its donor response and activity."
      />
    );
  }
  if (query.isPending) {
    return (
      <div
        aria-label="Loading follow-up detail"
        className="bg-surface-muted h-96 animate-pulse rounded"
      />
    );
  }
  if (query.error || !query.data) {
    return (
      <ErrorState
        description="The follow-up details could not be loaded."
        onRetry={() => void query.refetch()}
      />
    );
  }
  return (
    <aside className="border-border bg-surface rounded-card space-y-6 border p-5">
      <FollowUpDetailContent detail={query.data} />
      <section className="border-border border-t pt-5">
        <FollowUpActions detail={query.data} />
      </section>
    </aside>
  );
}
