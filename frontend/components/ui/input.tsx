import * as React from "react";

import { cn } from "@/lib/utils/class-names";

/** Shared text input primitive. */
export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>): React.JSX.Element {
  return (
    <input
      className={cn(
        "border-border bg-surface text-foreground placeholder:text-muted-foreground rounded-control focus-visible:outline-ring h-10 w-full border px-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
