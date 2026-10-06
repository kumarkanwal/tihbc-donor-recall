import { Copy } from "lucide-react";

import { DateTime } from "@/components/shared/date-time";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import type { FollowUpDetail } from "@/lib/api/contracts";
import { showToast } from "@/lib/toast/store";

function valueOrDash(value: string | null | undefined): string {
  return value || "—";
}

/** Donor, response, appointment, and activity context for a follow-up. */
export function FollowUpDetailContent({
  detail,
}: {
  detail: FollowUpDetail;
}): React.JSX.Element {
  return (
    <div className="space-y-6">
      <section>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">{detail.donor.name}</h2>
            <p className="text-muted-foreground mt-1">{detail.donor.phone}</p>
          </div>
          <Button
            type="button"
            size="small"
            variant="secondary"
            onClick={() => {
              void navigator.clipboard.writeText(detail.donor.phone);
              showToast("Phone number copied");
            }}
          >
            <Copy aria-hidden="true" />
            Copy number
          </Button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <StatusBadge status={detail.type} />
          <StatusBadge status={detail.status} />
          <StatusBadge status={detail.priority} />
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <Info label="Segment" value={detail.donor.segment} />
          <Info label="Language" value={detail.donor.language.toUpperCase()} />
          <Info label="City" value={valueOrDash(detail.donor.city)} />
          <Info
            label="Blood group"
            value={valueOrDash(detail.donor.blood_group)}
          />
        </dl>
      </section>
      <section className="border-border border-t pt-5">
        <h3 className="font-semibold">Response</h3>
        {detail.latest_response ? (
          <div className="mt-3 space-y-2 text-sm">
            <p className="rounded-control bg-surface-muted p-3">
              {detail.latest_response.raw_text}
            </p>
            <Info
              label="Detected intent"
              value={detail.latest_response.intent}
            />
            <Info
              label="Requested date"
              value={valueOrDash(detail.latest_response.requested_date)}
            />
            <Info
              label="Decline reason"
              value={valueOrDash(detail.latest_response.decline_reason)}
            />
          </div>
        ) : (
          <p className="text-muted-foreground mt-2 text-sm">
            No classified response yet.
          </p>
        )}
        {detail.appointment ? (
          <p className="mt-3 text-sm">
            Booked at {detail.appointment.center_name},{" "}
            <DateTime value={detail.appointment.slot_start} />
          </p>
        ) : null}
      </section>
      <section className="border-border border-t pt-5">
        <h3 className="font-semibold">Activity</h3>
        {detail.activities.length ? (
          <ol className="mt-3 space-y-3">
            {detail.activities.map((activity) => (
              <li
                key={activity.id}
                className="border-border border-l-2 pl-3 text-sm"
              >
                <p className="font-medium">
                  {activity.action.replaceAll("_", " ")}
                </p>
                {activity.note ? <p className="mt-1">{activity.note}</p> : null}
                <p className="text-muted-foreground mt-1 text-xs">
                  {activity.user_name ?? "System"} ·{" "}
                  <DateTime value={activity.created_at} />
                </p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-muted-foreground mt-2 text-sm">
            No activity has been recorded.
          </p>
        )}
      </section>
    </div>
  );
}

function Info({
  label,
  value,
}: {
  label: string;
  value: string;
}): React.JSX.Element {
  return (
    <div>
      <dt className="text-muted-foreground text-xs">{label}</dt>
      <dd className="mt-0.5 capitalize">{value.replaceAll("_", " ")}</dd>
    </div>
  );
}
