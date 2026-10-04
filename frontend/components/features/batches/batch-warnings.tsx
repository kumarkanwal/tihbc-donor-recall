import { AlertTriangle } from "lucide-react";

import type { BatchPreview } from "@/hooks/use-donor-batches";

/** Show cross-batch matches as context, never as validation failures. */
export function BatchWarnings({
  warnings,
}: Pick<BatchPreview, "warnings">): React.JSX.Element | null {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <section className="border-warning/40 bg-warning/10 rounded-card border p-5">
      <div className="flex items-start gap-3">
        <AlertTriangle
          className="text-warning mt-0.5 size-5 shrink-0"
          aria-hidden="true"
        />
        <div>
          <h3 className="font-semibold">Existing donors found</h3>
          <p className="text-muted-foreground mt-1 text-sm">
            These rows are valid and will be imported. Their phone numbers also
            appear in an earlier batch.
          </p>
        </div>
      </div>
      <ul className="mt-4 space-y-2 text-sm">
        {warnings.map((warning) => (
          <li
            key={`${warning.row}-${warning.phone}`}
            className="border-warning/30 bg-surface rounded-control border px-3 py-2"
          >
            Row {warning.row}:{" "}
            <span className="font-mono">{warning.phone}</span> also appears in{" "}
            <span className="font-medium">{warning.existing_batch_name}</span>.
          </li>
        ))}
      </ul>
    </section>
  );
}
