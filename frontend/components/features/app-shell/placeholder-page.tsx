import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

/** Temporary route content until its feature task is implemented. */
export function PlaceholderPage({
  title,
  description,
}: PlaceholderPageProps): React.JSX.Element {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />
      <EmptyState
        title="Coming soon"
        description={`${title} will be available in an upcoming task.`}
      />
    </div>
  );
}
