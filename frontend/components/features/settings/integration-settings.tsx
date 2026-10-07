import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { useIntegrationSettings } from "@/hooks/use-settings";

function displayValue(value: string | number): string {
  return typeof value === "number" ? value.toLocaleString() : value;
}

/** Mocked WhatsApp Business configuration and approved template status. */
export function IntegrationSettings(): React.JSX.Element {
  const query = useIntegrationSettings();

  if (query.error) {
    return (
      <ErrorState
        description="Integration settings could not be loaded."
        onRetry={() => void query.refetch()}
      />
    );
  }
  if (!query.data) {
    return <div className="bg-surface-muted rounded-card h-64 animate-pulse" />;
  }

  const rows = [
    [
      "Business verification",
      query.data.business_verified ? "Verified" : "Not verified",
    ],
    ["Phone number", query.data.phone_number],
    ["Display name", query.data.display_name],
    ["Quality rating", query.data.quality_rating],
    ["Messaging limit", displayValue(query.data.messaging_limit)],
  ] as const;

  return (
    <div className="space-y-6">
      <section className="rounded-card border-border bg-surface shadow-surface border p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">WhatsApp integration</h2>
            <p className="text-muted-foreground mt-1 text-sm">
              Business account and sending status
            </p>
          </div>
          <StatusBadge status="draft" label="Demo environment" />
        </div>
        <dl className="divide-border mt-5 divide-y">
          {rows.map(([label, value]) => (
            <div
              key={label}
              className="grid gap-1 py-3 sm:grid-cols-[14rem_1fr]"
            >
              <dt className="text-muted-foreground text-sm">{label}</dt>
              <dd className="text-sm font-medium">{value}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section className="rounded-card border-border bg-surface shadow-surface overflow-hidden border">
        <header className="px-5 py-4">
          <h2 className="text-lg font-semibold">Message templates</h2>
          <p className="text-muted-foreground text-sm">
            Mocked provider approval status
          </p>
        </header>
        {query.data.templates.length ? (
          <table className="w-full text-left text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Category</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {query.data.templates.map((template) => (
                <tr
                  key={template.step_id}
                  className="border-border hover:bg-surface-muted focus-within:bg-surface-muted relative border-t transition-colors"
                >
                  <td className="px-5 py-3 font-medium">{template.name}</td>
                  <td className="px-5 py-3 capitalize">{template.category}</td>
                  <td className="px-5 py-3">
                    <StatusBadge
                      status={
                        template.status === "approved"
                          ? "active"
                          : template.status
                      }
                      label={template.status}
                    />
                    <Link
                      href={`/series/${template.series_id}?step=${template.step_id}`}
                      aria-label={`Open ${template.name} in Content Series`}
                      className="focus-visible:outline-ring absolute inset-0 cursor-pointer rounded focus-visible:outline-2 focus-visible:outline-offset-[-2px]"
                    >
                      <span className="sr-only">
                        Open {template.name} in Content Series
                      </span>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState
            title="No templates"
            description="Template status will appear here when configured."
            className="min-h-52 rounded-none border-0 border-t"
          />
        )}
      </section>
    </div>
  );
}
