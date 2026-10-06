"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/shared/chart-card";
import type { MetricsTimeseriesItem } from "@/lib/api/contracts";

interface DailyActivityChartProps {
  items?: MetricsTimeseriesItem[];
  isLoading: boolean;
  error?: string;
  onRetry: () => void;
}

/** Daily messaging activity rendered with theme-aware design tokens. */
export function DailyActivityChart({
  items = [],
  isLoading,
  error,
  onRetry,
}: DailyActivityChartProps): React.JSX.Element {
  return (
    <ChartCard
      title="Daily activity"
      description="Messages and responses by day"
      isLoading={isLoading}
      isEmpty={items.length === 0}
      error={error}
      onRetry={onRetry}
    >
      <div className="h-72" aria-label="Daily activity chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={items} margin={{ left: -16, right: 8 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="date" stroke="var(--muted-foreground)" />
            <YAxis stroke="var(--muted-foreground)" allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                borderColor: "var(--border)",
                borderRadius: "var(--control-radius)",
              }}
            />
            <Legend />
            <Line dataKey="sent" stroke="var(--primary)" strokeWidth={2} />
            <Line dataKey="delivered" stroke="var(--info)" strokeWidth={2} />
            <Line dataKey="read" stroke="var(--success)" strokeWidth={2} />
            <Line dataKey="responded" stroke="var(--accent)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
