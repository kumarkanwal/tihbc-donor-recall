"use client";

import { useDemoNow } from "@/lib/demo-time";

const displayTimeZone = "Asia/Karachi";

interface DateTimeProps {
  value: string | Date;
  relative?: boolean;
  now?: Date;
}

function toDate(value: string | Date): Date {
  return value instanceof Date ? value : new Date(value);
}

/** Format a timestamp for TIHBC staff in Asia/Karachi. */
export function formatDateTime(value: string | Date): string {
  const date = toDate(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-GB", {
    timeZone: displayTimeZone,
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  })
    .format(date)
    .replace(/\b(am|pm)\b/, (period) => period.toUpperCase());
}

function formatRelative(value: Date, now: Date): string {
  const seconds = Math.round((value.getTime() - now.getTime()) / 1000);
  const absoluteSeconds = Math.abs(seconds);
  const [amount, unit] =
    absoluteSeconds < 60
      ? [seconds, "second"]
      : absoluteSeconds < 3600
        ? [Math.round(seconds / 60), "minute"]
        : absoluteSeconds < 86400
          ? [Math.round(seconds / 3600), "hour"]
          : [Math.round(seconds / 86400), "day"];

  return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
    amount,
    unit as Intl.RelativeTimeFormatUnit,
  );
}

/** Render an absolute staff timestamp or a relative label with absolute tooltip. */
export function DateTime({
  value,
  relative = false,
  now,
}: DateTimeProps): React.JSX.Element {
  const demoNow = useDemoNow();
  const date = toDate(value);
  const absolute = formatDateTime(date);
  const referenceTime = now ?? demoNow;
  const label =
    relative && absolute !== "—" && referenceTime
      ? formatRelative(date, referenceTime)
      : absolute;

  return (
    <time
      dateTime={Number.isNaN(date.getTime()) ? undefined : date.toISOString()}
      title={absolute}
    >
      {label}
    </time>
  );
}
