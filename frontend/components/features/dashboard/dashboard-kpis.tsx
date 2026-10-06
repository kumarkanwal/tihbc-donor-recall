import { KpiCard } from "@/components/shared/kpi-card";
import type { MetricsOverview } from "@/lib/api/contracts";

interface DashboardKpisProps {
  metrics: MetricsOverview;
}

function percentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

/** Six headline measures used by staff during campaign monitoring. */
export function DashboardKpis({
  metrics,
}: DashboardKpisProps): React.JSX.Element {
  return (
    <section
      aria-label="Campaign performance summary"
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
    >
      <KpiCard
        testId="dashboard-kpi-donors-reached"
        label="Donors reached"
        value={metrics.donors.toLocaleString()}
        subValue={`${metrics.sent.toLocaleString()} messages sent`}
      />
      <KpiCard
        testId="dashboard-kpi-delivery-rate"
        label="Delivery rate"
        value={percentage(metrics.delivery_rate)}
        subValue={`${metrics.delivered.toLocaleString()} delivered`}
      />
      <KpiCard
        testId="dashboard-kpi-read-rate"
        label="Read rate"
        value={percentage(metrics.read_rate)}
        subValue={`${metrics.read.toLocaleString()} read`}
      />
      <KpiCard
        testId="dashboard-kpi-response-rate"
        label="Response rate"
        value={percentage(metrics.response_rate)}
        subValue={`${metrics.responded.toLocaleString()} responded`}
      />
      <KpiCard
        testId="dashboard-kpi-confirmed"
        label="Confirmed"
        value={metrics.confirmed.toLocaleString()}
      />
      <KpiCard
        testId="dashboard-kpi-needs-call"
        label="Needs call"
        value={metrics.escalated.toLocaleString()}
        subValue="Escalated to a coordinator"
      />
    </section>
  );
}
