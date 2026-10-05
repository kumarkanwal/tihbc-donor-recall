import Link from "next/link";

import { DateTime } from "@/components/shared/date-time";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import type { FollowUpListItem } from "@/lib/api/pending-contracts";

interface RecentFollowUpsProps {
  items?: FollowUpListItem[];
}

/** Latest open coordinator work, limited by the dashboard query. */
export function RecentFollowUps({
  items = [],
}: RecentFollowUpsProps): React.JSX.Element {
  return (
    <section className="rounded-card border-border bg-surface shadow-surface border p-5">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Recent follow-ups</h2>
          <p className="text-muted-foreground text-sm">
            Latest open donor work
          </p>
        </div>
        <Link className="text-primary text-sm font-medium" href="/inbox">
          Open inbox
        </Link>
      </header>
      {items.length === 0 ? (
        <EmptyState
          title="No open follow-ups"
          description="New donor responses will appear here."
          className="mt-4 min-h-48 border-0 p-4"
        />
      ) : (
        <ul className="divide-border mt-4 divide-y">
          {items.slice(0, 5).map((item) => (
            <li key={item.id} className="flex items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {item.donor.name}
                </p>
                <p className="text-muted-foreground truncate text-xs">
                  {item.campaign.name}
                </p>
              </div>
              <StatusBadge status={item.type} />
              <span className="text-muted-foreground text-xs">
                <DateTime value={item.updated_at} relative />
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
