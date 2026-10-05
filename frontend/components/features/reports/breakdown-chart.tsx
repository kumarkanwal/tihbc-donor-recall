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

interface BreakdownChartProps {
  title: string;
  description: string;
  values: Record<string, number>;
}

function label(value: string): string {
  if (value === "en") return "English";
  if (value === "ur") return "Urdu";
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

/** Reusable theme-aware bar chart for one aggregate dimension. */
export function BreakdownChart({
  title,
  description,
  values,
}: BreakdownChartProps): React.JSX.Element {
  const data = Object.entries(values).map(([name, count]) => ({
    name: label(name),
    count,
  }));

  return (
    <ChartCard
      title={title}
      description={description}
      isEmpty={data.length === 0}
    >
      <div className="h-64" aria-label={`${title} chart`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: -16, right: 8 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="name" stroke="var(--muted-foreground)" />
            <YAxis stroke="var(--muted-foreground)" allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                borderColor: "var(--border)",
                borderRadius: "var(--control-radius)",
              }}
            />
            <Bar dataKey="count" fill="var(--primary)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
