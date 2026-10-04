import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumb?: ReactNode;
  actions?: ReactNode;
}

/** Consistent heading area for application pages. */
export function PageHeader({
  title,
  description,
  breadcrumb,
  actions,
}: PageHeaderProps): React.JSX.Element {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        {breadcrumb ? (
          <div className="text-muted-foreground mb-2 text-xs">{breadcrumb}</div>
        ) : null}
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description ? (
          <p className="text-muted-foreground mt-1 max-w-3xl">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 gap-2">{actions}</div> : null}
    </header>
  );
}
