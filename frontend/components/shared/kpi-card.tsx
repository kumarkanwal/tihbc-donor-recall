import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils/class-names";

type TrendDirection = "up" | "down" | "neutral";
type TrendTone = "positive" | "negative" | "neutral";

interface KpiTrend {
  value: string;
  direction?: TrendDirection;
  tone?: TrendTone;
}

interface KpiCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  trend?: KpiTrend;
}

const trendIcons = {
  up: ArrowUpRight,
  down: ArrowDownRight,
  neutral: ArrowRight,
} as const;

const trendStyles = {
  positive: "text-success",
  negative: "text-danger",
  neutral: "text-muted-foreground",
} as const;

/** Display one dashboard metric and optional contextual trend. */
export function KpiCard({
  label,
  value,
  subValue,
  trend,
}: KpiCardProps): React.JSX.Element {
  const TrendIcon = trendIcons[trend?.direction ?? "neutral"];

  return (
    <article className="rounded-card border-border bg-surface shadow-surface border p-5">
      <p className="text-muted-foreground text-sm font-medium">{label}</p>
      <p className="mt-2 text-[1.75rem] leading-tight font-semibold tabular-nums">
        {value}
      </p>
      <div className="mt-2 flex min-h-5 items-center gap-3 text-xs">
        {subValue ? (
          <span className="text-muted-foreground">{subValue}</span>
        ) : null}
        {trend ? (
          <span
            className={cn(
              "inline-flex items-center gap-1 font-medium",
              trendStyles[trend.tone ?? "neutral"],
            )}
          >
            <TrendIcon
              aria-hidden="true"
              className="size-3.5"
              strokeWidth={1.75}
            />
            {trend.value}
          </span>
        ) : null}
      </div>
    </article>
  );
}
