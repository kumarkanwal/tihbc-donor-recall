import type { EnrollmentStatus } from "@/hooks/use-campaigns";
import { cn } from "@/lib/utils/class-names";

export const enrollmentStatuses: EnrollmentStatus[] = [
  "pending",
  "in_primary",
  "in_secondary",
  "escalated",
  "confirmed",
  "reschedule_requested",
  "rescheduled",
  "declined",
  "invalid_number",
  "undeliverable",
];

function label(status: EnrollmentStatus): string {
  return status
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

/** Clickable campaign enrollment counters, including zero-count statuses. */
export function EnrollmentStatusCards({
  counts,
  selected,
  onSelect,
}: {
  counts: Record<string, number>;
  selected: EnrollmentStatus | undefined;
  onSelect: (status: EnrollmentStatus | undefined) => void;
}): React.JSX.Element {
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Enrollment status</h2>
        {selected ? (
          <button
            type="button"
            className="text-primary text-sm font-medium"
            onClick={() => onSelect(undefined)}
          >
            Clear filter
          </button>
        ) : null}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {enrollmentStatuses.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => onSelect(status)}
            className={cn(
              "rounded-card border-border bg-surface border p-4 text-left transition-colors",
              selected === status && "border-primary ring-primary/20 ring-2",
            )}
          >
            <span className="text-muted-foreground text-xs">
              {label(status)}
            </span>
            <span className="mt-1 block text-2xl font-semibold tabular-nums">
              {counts[status] ?? 0}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
