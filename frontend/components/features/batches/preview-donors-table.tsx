import type { components } from "@/lib/api/schema";

type DonorPreviewRow = components["schemas"]["DonorPreviewRow"];

const languageLabels = { en: "English", ur: "Urdu" } as const;

/** Display the normalized valid-row sample returned by the preview API. */
export function PreviewDonorsTable({
  donors,
}: {
  donors: DonorPreviewRow[];
}): React.JSX.Element {
  if (donors.length === 0) {
    return (
      <div className="border-border bg-surface rounded-card border p-6 text-center">
        <p className="font-medium">No valid rows to preview</p>
        <p className="text-muted-foreground mt-1 text-sm">
          Correct the file errors and upload it again.
        </p>
      </div>
    );
  }

  return (
    <section className="border-border bg-surface rounded-card overflow-hidden border">
      <div className="border-border border-b p-4">
        <h3 className="font-semibold">First {donors.length} valid rows</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="bg-surface-muted">
            <tr>
              {[
                "Row",
                "Name",
                "Phone",
                "Segment",
                "Language",
                "City",
                "Blood group",
              ].map((heading) => (
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
            {donors.map((donor) => (
              <tr key={donor.row}>
                <td className="border-border border-b px-4 py-3 tabular-nums">
                  {donor.row}
                </td>
                <td className="border-border border-b px-4 py-3 font-medium">
                  {donor.name}
                </td>
                <td className="border-border border-b px-4 py-3 font-mono">
                  {donor.phone}
                </td>
                <td className="border-border border-b px-4 py-3 capitalize">
                  {donor.segment.replaceAll("_", " ")}
                </td>
                <td className="border-border border-b px-4 py-3">
                  {languageLabels[donor.language]}
                </td>
                <td className="border-border border-b px-4 py-3">
                  {donor.city || "—"}
                </td>
                <td className="border-border border-b px-4 py-3">
                  {donor.blood_group || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
