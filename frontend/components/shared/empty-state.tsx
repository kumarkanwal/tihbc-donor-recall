import { Inbox, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils/class-names";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: LucideIcon;
  className?: string;
}

/** Friendly empty-data state with an optional primary action. */
export function EmptyState({
  title,
  description,
  action,
  icon: Icon = Inbox,
  className,
}: EmptyStateProps): React.JSX.Element {
  return (
    <section
      className={cn(
        "rounded-card border-border bg-surface flex min-h-72 flex-col items-center justify-center border p-8 text-center",
        className,
      )}
    >
      <span className="bg-primary-soft text-primary flex size-12 items-center justify-center rounded-full">
        <Icon aria-hidden="true" className="size-5" strokeWidth={1.75} />
      </span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="text-muted-foreground mt-1 max-w-md">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </section>
  );
}
