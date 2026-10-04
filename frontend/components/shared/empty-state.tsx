import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

/** Friendly empty-data state with an optional primary action. */
export function EmptyState({
  title,
  description,
  action,
}: EmptyStateProps): React.JSX.Element {
  return (
    <section className="rounded-card border-border bg-surface flex min-h-72 flex-col items-center justify-center border p-8 text-center">
      <span className="bg-primary-soft text-primary flex size-12 items-center justify-center rounded-full">
        <Inbox aria-hidden="true" className="size-5" strokeWidth={1.75} />
      </span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="text-muted-foreground mt-1 max-w-md">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </section>
  );
}
