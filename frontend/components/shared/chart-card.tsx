import type { ReactNode } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";

interface ChartCardProps {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  isLoading?: boolean;
  isEmpty?: boolean;
  error?: string;
  onRetry?: () => void;
}

/** Card boundary that gives charts all required view states. */
export function ChartCard({
  title,
  description,
  action,
  children,
  isLoading = false,
  isEmpty = false,
  error,
  onRetry,
}: ChartCardProps): React.JSX.Element {
  let content = children;

  if (isLoading) {
    content = (
      <div
        className="space-y-3 py-8"
        aria-label="Loading chart"
        aria-busy="true"
      >
        <div className="bg-surface-muted rounded-card h-48 animate-pulse" />
        <div className="bg-surface-muted mx-auto h-4 w-2/3 animate-pulse rounded" />
      </div>
    );
  } else if (error) {
    content = (
      <ErrorState
        description={error}
        onRetry={onRetry}
        className="min-h-64 border-0"
      />
    );
  } else if (isEmpty) {
    content = (
      <EmptyState
        title="No data yet"
        description="Data will appear here when activity is available."
        className="min-h-64 border-0"
      />
    );
  }

  return (
    <section className="rounded-card border-border bg-surface shadow-surface border p-5">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          {description ? (
            <p className="text-muted-foreground mt-1 text-sm">{description}</p>
          ) : null}
        </div>
        {action}
      </header>
      <div className="mt-5">{content}</div>
    </section>
  );
}
