import { CircleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  description: string;
  onRetry?: () => void;
}

/** Recoverable error message with an optional retry action. */
export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
}: ErrorStateProps): React.JSX.Element {
  return (
    <section className="rounded-card border-border bg-surface flex min-h-64 flex-col items-center justify-center border p-8 text-center">
      <span className="bg-accent-soft text-danger flex size-12 items-center justify-center rounded-full">
        <CircleAlert aria-hidden="true" className="size-5" strokeWidth={1.75} />
      </span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="text-muted-foreground mt-1 max-w-md">{description}</p>
      {onRetry ? (
        <Button
          type="button"
          variant="secondary"
          className="mt-5"
          onClick={onRetry}
        >
          Try again
        </Button>
      ) : null}
    </section>
  );
}
