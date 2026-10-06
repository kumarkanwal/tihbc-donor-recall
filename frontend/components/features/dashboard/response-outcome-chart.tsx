"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/shared/chart-card";
import type { MetricsOverview } from "@/lib/api/contracts";

interface ResponseOutcomeChartProps {
  metrics?: MetricsOverview;
  isLoading: boolean;
  error?: string;
  onRetry: () => void;
}

/** Compare donor outcomes, including donors who have not responded. */
export function ResponseOutcomeChart({
  metrics,
  isLoading,
  error,
  onRetry,
}: ResponseOutcomeChartProps): React.JSX.Element {
  const data = metrics
    ? [
        { name: "Confirmed", value: metrics.confirmed },
        { name: "Rescheduled", value: metrics.rescheduled },
        { name: "Declined", value: metrics.declined },
        {
          name: "No response",
          value: Math.max(metrics.donors - metrics.responded, 0),
        },
        { name: "Escalated", value: metrics.escalated },
      ]
    : [];

  return (
    <ChartCard
      title="Response outcomes"
      description="Current result for reached donors"
      isLoading={isLoading}
      isEmpty={data.length === 0}
      error={error}
      onRetry={onRetry}
    >
      <div className="h-72" aria-label="Response outcomes chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
            <CartesianGrid stroke="var(--border)" horizontal={false} />
            <XAxis
              type="number"
              stroke="var(--muted-foreground)"
              allowDecimals={false}
            />
            <YAxis
              dataKey="name"
              type="category"
              stroke="var(--muted-foreground)"
              width={88}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                borderColor: "var(--border)",
                borderRadius: "var(--control-radius)",
              }}
            />
            <Bar
              dataKey="value"
              name="Donors"
              fill="var(--primary)"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
