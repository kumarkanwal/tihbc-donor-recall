import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { SeriesStep } from "@/hooks/use-content-series";

/** Heading and close control for the series-step drawer. */
export function SeriesStepDrawerHeader({
  step,
  onClose,
}: {
  step: SeriesStep | null;
  onClose: () => void;
}): React.JSX.Element {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h2 id="step-drawer-title" className="text-xl font-semibold">
          {step ? `Edit step ${step.step_order}` : "Add step"}
        </h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Set the timing, message, media, and quick replies.
        </p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Close step editor"
        onClick={onClose}
      >
        <X aria-hidden="true" />
      </Button>
    </div>
  );
}
