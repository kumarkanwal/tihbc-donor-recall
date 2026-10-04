import { AlertCircle, Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { downloadValidationReport } from "@/components/features/batches/batch-files";
import type { ValidationIssue } from "@/hooks/use-donor-batches";

interface ValidationIssuesTableProps {
  issues: ValidationIssue[];
  allowDownload?: boolean;
}

/** Render row-level import errors with an optional local CSV export. */
export function ValidationIssuesTable({
  issues,
  allowDownload = false,
}: ValidationIssuesTableProps): React.JSX.Element {
  if (issues.length === 0) {
    return (
      <div className="border-border bg-surface rounded-card border p-6 text-center">
        <p className="font-medium">No validation errors</p>
        <p className="text-muted-foreground mt-1 text-sm">
          Every row in this batch passed validation.
        </p>
      </div>
    );
  }

  return (
    <section className="border-border bg-surface rounded-card overflow-hidden border">
      <div className="border-border flex items-center justify-between gap-4 border-b p-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="text-danger size-5" aria-hidden="true" />
          <h3 className="font-semibold">Validation errors</h3>
        </div>
        {allowDownload ? (
          <Button
            type="button"
            variant="secondary"
            size="small"
            onClick={() => downloadValidationReport(issues)}
          >
            <Download aria-hidden="true" />
            Download error report
          </Button>
        ) : null}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-surface-muted">
            <tr>
              {["Row", "Field", "Value", "Reason"].map((heading) => (
                <th
                  key={heading}
                  className="border-border border-b px-4 py-3 font-medium"
                >
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {issues.map((issue, index) => (
              <tr key={`${issue.row}-${issue.field}-${index}`}>
                <td className="border-border border-b px-4 py-3 tabular-nums">
                  {issue.row}
                </td>
                <td className="border-border border-b px-4 py-3">
                  {issue.field}
                </td>
                <td className="border-border max-w-56 border-b px-4 py-3 break-words">
                  {issue.value || "—"}
                </td>
                <td className="border-border border-b px-4 py-3">
                  {issue.reason}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
