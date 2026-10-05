import type { ContentSeriesDetail } from "@/hooks/use-content-series";

interface ScheduleItem {
  key: string;
  day: number;
  label: string;
  detail: string;
}

function responseDays(hours: number): number {
  return Math.ceil(hours / 24);
}

function buildSchedule(
  primary?: ContentSeriesDetail,
  secondary?: ContentSeriesDetail,
): ScheduleItem[] {
  if (!primary || !secondary) return [];
  const primaryLastDay = Math.max(
    0,
    ...primary.steps.map((step) => step.delay_days),
  );
  const secondaryStart =
    primaryLastDay + responseDays(primary.response_window_hours);
  const secondaryLastDay = Math.max(
    0,
    ...secondary.steps.map((step) => step.delay_days),
  );
  const items = primary.steps.map((step) => ({
    key: `primary-${step.id}`,
    day: step.delay_days,
    label: `Primary · Step ${step.step_order}`,
    detail: `${step.category} message`,
  }));
  items.push(
    ...secondary.steps.map((step) => ({
      key: `secondary-${step.id}`,
      day: secondaryStart + step.delay_days,
      label: `Secondary · Step ${step.step_order}`,
      detail: `${step.category} message`,
    })),
  );
  items.push({
    key: "escalation",
    day:
      secondaryStart +
      secondaryLastDay +
      responseDays(secondary.response_window_hours),
    label: "Escalate to coordinator",
    detail: "Create a needs-call follow-up",
  });
  return items;
}

/** Combined primary, secondary, and coordinator-escalation schedule. */
export function CampaignScheduleTimeline({
  primary,
  secondary,
  placeholder = "Select both series to preview the schedule.",
}: {
  primary?: ContentSeriesDetail;
  secondary?: ContentSeriesDetail;
  placeholder?: string;
}): React.JSX.Element {
  const items = buildSchedule(primary, secondary);
  if (items.length === 0) {
    return <p className="text-muted-foreground text-sm">{placeholder}</p>;
  }
  return (
    <ol className="border-border ml-2 space-y-4 border-l pl-5">
      {items.map((item) => (
        <li key={item.key} className="relative">
          <span className="bg-primary absolute top-1.5 -left-[1.48rem] size-2 rounded-full" />
          <p className="text-sm font-medium">
            Day {item.day} · {item.label}
          </p>
          <p className="text-muted-foreground text-xs capitalize">
            {item.detail}
          </p>
        </li>
      ))}
    </ol>
  );
}
