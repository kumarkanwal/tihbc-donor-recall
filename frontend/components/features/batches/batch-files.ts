import type { ValidationIssue } from "@/hooks/use-donor-batches";

function escapeCsvCell(value: string | number): string {
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/** Start a browser download for a generated or API-provided file. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

/** Generate the review error report without sending donor data elsewhere. */
export function downloadValidationReport(errors: ValidationIssue[]): void {
  const rows = [
    ["row", "field", "value", "reason"],
    ...errors.map((issue) => [
      issue.row,
      issue.field,
      issue.value,
      issue.reason,
    ]),
  ];
  const csv = rows
    .map((row) => row.map((cell) => escapeCsvCell(cell)).join(","))
    .join("\r\n");
  downloadBlob(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
    "donor-batch-errors.csv",
  );
}
