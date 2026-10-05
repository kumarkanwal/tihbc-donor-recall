"use client";

import { RotateCcw } from "lucide-react";

import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import {
  formatDemoClock,
  isDemoClockUnavailable,
  useAdvanceDemoClock,
  useDemoClock,
  useResetDemoClock,
} from "@/hooks/use-demo-clock";
import { useResetDemoData } from "@/hooks/use-settings";

const skipOptions = [
  { label: "+1 hour", days: 0, hours: 1 },
  { label: "+1 day", days: 1, hours: 0 },
  { label: "+3 days", days: 3, hours: 0 },
  { label: "+7 days", days: 7, hours: 0 },
] as const;

/** Administrator-only clock and seeded-data controls for presentations. */
export function DemoSettings(): React.JSX.Element {
  const clock = useDemoClock();
  const advance = useAdvanceDemoClock();
  const resetClock = useResetDemoClock();
  const resetData = useResetDemoData();
  const clockPending = advance.isPending || resetClock.isPending;

  if (isDemoClockUnavailable(clock.error)) {
    return (
      <EmptyState
        title="Available after backend update"
        description="Demo controls will be connected after backend Task 2.12."
      />
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-card border-border bg-surface shadow-surface border p-5">
        <h2 className="text-lg font-semibold">Demo clock</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Advance scheduled campaign activity during a presentation.
        </p>
        <div className="bg-surface-muted rounded-control mt-5 p-4">
          <p className="text-muted-foreground text-xs font-medium uppercase">
            Current demo time (Asia/Karachi)
          </p>
          <p className="mt-1 text-lg font-semibold">
            {clock.data ? formatDemoClock(clock.data.now) : "Loading time"}
          </p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {skipOptions.map((option) => (
            <Button
              key={option.label}
              type="button"
              variant="secondary"
              disabled={clockPending || clock.isPending || Boolean(clock.error)}
              onClick={() =>
                advance.mutate({ days: option.days, hours: option.hours })
              }
            >
              {option.label}
            </Button>
          ))}
          <Button
            type="button"
            variant="secondary"
            disabled={clockPending || clock.isPending || Boolean(clock.error)}
            onClick={() => resetClock.mutate()}
          >
            <RotateCcw aria-hidden="true" />
            Reset clock
          </Button>
        </div>
        {clock.error && !isDemoClockUnavailable(clock.error) ? (
          <p role="alert" className="text-danger mt-3 text-sm">
            The demo clock could not be loaded.
          </p>
        ) : null}
      </section>
      <section className="rounded-card border-danger/30 bg-surface border p-5">
        <h2 className="text-lg font-semibold">Reset demo data</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Restore seeded donors, series, campaigns, messages, and follow-ups.
        </p>
        <ConfirmDialog
          trigger={
            <Button type="button" variant="destructive" className="mt-5">
              <RotateCcw aria-hidden="true" />
              Reset demo data
            </Button>
          }
          title="Reset all demo data?"
          description="This replaces current demo activity with the original seeded data. This action cannot be undone."
          confirmLabel="Reset demo data"
          destructive
          pending={resetData.isPending}
          onConfirm={() => resetData.mutate()}
        />
        {resetData.error ? (
          <p role="alert" className="text-danger mt-3 text-sm">
            Demo data could not be reset. The backend update may not be
            available yet.
          </p>
        ) : null}
      </section>
    </div>
  );
}
