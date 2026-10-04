import { cn } from "@/lib/utils/class-names";

const statusStyles = {
  confirmed: "bg-success/12 text-success",
  rescheduled: "bg-success/12 text-success",
  delivered: "bg-success/12 text-success",
  read: "bg-success/12 text-success",
  done: "bg-success/12 text-success",
  completed: "bg-success/12 text-success",
  pending: "bg-warning/12 text-warning",
  reschedule_requested: "bg-warning/12 text-warning",
  scheduled: "bg-warning/12 text-warning",
  queued: "bg-warning/12 text-warning",
  open: "bg-warning/12 text-warning",
  in_primary: "bg-info/12 text-info",
  in_secondary: "bg-info/12 text-info",
  running: "bg-info/12 text-info",
  sent: "bg-info/12 text-info",
  in_progress: "bg-info/12 text-info",
  declined: "bg-danger/12 text-danger",
  failed: "bg-danger/12 text-danger",
  invalid_number: "bg-danger/12 text-danger",
  undeliverable: "bg-danger/12 text-danger",
  escalated: "bg-accent/12 text-accent",
  needs_call: "bg-accent/12 text-accent",
  draft: "border border-border bg-surface-muted text-muted-foreground",
  paused: "border border-border bg-surface-muted text-muted-foreground",
  archived: "border border-border bg-surface-muted text-muted-foreground",
} as const;

export type Status = keyof typeof statusStyles;

interface StatusBadgeProps {
  status: Status;
  label?: string;
  className?: string;
}

function formatStatus(status: Status): string {
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Render a domain status with the shared semantic color map. */
export function StatusBadge({
  status,
  label,
  className,
}: StatusBadgeProps): React.JSX.Element {
  return (
    <span
      className={cn(
        "rounded-control inline-flex items-center px-2.5 py-1 text-xs font-medium",
        statusStyles[status],
        className,
      )}
    >
      {label ?? formatStatus(status)}
    </span>
  );
}
