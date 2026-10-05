"use client";

import { X } from "lucide-react";

import { DateTime } from "@/components/shared/date-time";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { getCampaignErrorMessage, useEnrollment } from "@/hooks/use-campaigns";

/** Full donor enrollment details and related activity drawer. */
export function EnrollmentDrawer({
  enrollmentId,
  onClose,
}: {
  enrollmentId: string | null;
  onClose: () => void;
}): React.JSX.Element | null {
  const query = useEnrollment(enrollmentId);
  if (!enrollmentId) return null;
  const enrollment = query.data;
  return (
    <div
      className="bg-foreground/20 fixed inset-0 z-50"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="enrollment-title"
        className="border-border bg-surface absolute top-0 right-0 h-full w-full max-w-xl overflow-y-auto border-l p-6 shadow-xl"
      >
        <header className="flex items-start justify-between gap-4">
          <div>
            <h2 id="enrollment-title" className="text-xl font-semibold">
              Enrollment details
            </h2>
            <p className="text-muted-foreground mt-1 text-sm">
              Donor activity for this campaign.
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close enrollment details"
          >
            <X aria-hidden="true" />
          </Button>
        </header>
        {query.isPending ? (
          <div
            aria-label="Loading enrollment"
            className="bg-surface-muted mt-6 h-80 animate-pulse rounded"
          />
        ) : null}
        {query.error ? (
          <ErrorState
            className="mt-6"
            title="Could not load enrollment"
            description={getCampaignErrorMessage(
              query.error,
              "The enrollment could not be loaded.",
            )}
            onRetry={() => void query.refetch()}
          />
        ) : null}
        {enrollment ? (
          <div className="mt-6 space-y-6">
            <section className="rounded-card border-border grid gap-4 border p-4 sm:grid-cols-2">
              <Detail label="Donor" value={enrollment.donor.full_name} />
              <Detail label="Phone" value={enrollment.donor.phone_e164} mono />
              <Detail
                label="Language"
                value={enrollment.donor.language.toUpperCase()}
              />
              <Detail label="Segment" value={enrollment.donor.segment} />
              <div>
                <p className="text-muted-foreground text-xs">Status</p>
                <StatusBadge status={enrollment.status} className="mt-1" />
              </div>
              <Detail
                label="Current step"
                value={
                  enrollment.current_step_order
                    ? `${enrollment.current_series_kind} · Step ${enrollment.current_step_order}`
                    : "Not started"
                }
              />
            </section>
            <section>
              <h3 className="font-semibold">Messages and responses</h3>
              {enrollment.timeline.length === 0 ? (
                <EmptyState
                  className="mt-3 min-h-40"
                  title="No activity yet"
                  description="Messages and donor responses will appear here."
                />
              ) : (
                <ol className="border-border mt-3 space-y-4 border-l pl-5">
                  {enrollment.timeline.map((item) => (
                    <li key={item.id}>
                      <p className="text-sm font-medium">
                        {item.type === "message"
                          ? `Message · ${item.message?.status ?? "queued"}`
                          : `Response · ${item.response?.intent ?? "unknown"}`}
                      </p>
                      <p className="text-muted-foreground text-xs">
                        <DateTime value={item.created_at} />
                      </p>
                      {item.message ? (
                        <p className="mt-1 text-sm">{item.message.body}</p>
                      ) : null}
                    </li>
                  ))}
                </ol>
              )}
            </section>
            <section className="grid gap-4 sm:grid-cols-2">
              <InfoPanel title="Appointment">
                {enrollment.appointment ? (
                  <>
                    <p>{enrollment.appointment.center_name}</p>
                    <DateTime value={enrollment.appointment.starts_at} />
                  </>
                ) : (
                  <p>No appointment booked.</p>
                )}
              </InfoPanel>
              <InfoPanel title="Follow-up">
                {enrollment.follow_up ? (
                  <>
                    <StatusBadge status={enrollment.follow_up.status} />
                    <p className="mt-2 capitalize">
                      {enrollment.follow_up.type.replace("_", " ")} ·{" "}
                      {enrollment.follow_up.priority}
                    </p>
                  </>
                ) : (
                  <p>No follow-up linked.</p>
                )}
              </InfoPanel>
            </section>
          </div>
        ) : null}
      </aside>
    </div>
  );
}

function Detail({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}): React.JSX.Element {
  return (
    <div>
      <p className="text-muted-foreground text-xs">{label}</p>
      <p className={`mt-1 text-sm ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}

function InfoPanel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <div className="rounded-card border-border border p-4 text-sm">
      <h3 className="mb-2 font-semibold">{title}</h3>
      <div className="text-muted-foreground">{children}</div>
    </div>
  );
}
