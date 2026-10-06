import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MetricsOverview } from "@/lib/api/contracts";

import { DashboardScreen } from "./dashboard-screen";

const mocks = vi.hoisted(() => ({
  overview: vi.fn(),
  timeseries: vi.fn(),
  breakdown: vi.fn(),
  declineReasons: vi.fn(),
  campaignMetrics: vi.fn(),
  followUps: vi.fn(),
}));

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
    children,
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  CartesianGrid: () => null,
  Legend: () => null,
  Line: () => null,
  Bar: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));
vi.mock("@/hooks/use-campaigns", () => ({
  useCampaignCatalog: () => ({ data: { items: [] } }),
}));
vi.mock("@/hooks/use-follow-ups", () => ({ useFollowUps: mocks.followUps }));
vi.mock("@/hooks/use-metrics", () => ({
  useMetricsOverview: mocks.overview,
  useMetricsTimeseries: mocks.timeseries,
  useMetricsResponseBreakdown: mocks.breakdown,
  useDeclineReasons: mocks.declineReasons,
  useCampaignMetrics: mocks.campaignMetrics,
}));
const overview: MetricsOverview = {
  donors: 200,
  sent: 200,
  delivered: 190,
  read: 160,
  responded: 80,
  delivery_rate: 95,
  read_rate: 80,
  response_rate: 40,
  confirmed: 45,
  rescheduled: 20,
  declined: 15,
  escalated: 12,
  invalid_numbers: 3,
  undeliverable: 7,
};

function query(data: unknown = undefined) {
  return {
    data,
    isPending: false,
    error: null,
    refetch: vi.fn(),
  };
}

describe("DashboardScreen", () => {
  beforeEach(() => {
    mocks.overview.mockReturnValue(query(overview));
    mocks.timeseries.mockReturnValue(query({ items: [] }));
    mocks.breakdown.mockReturnValue(
      query({ by_intent: {}, by_segment: {}, by_language: {} }),
    );
    mocks.declineReasons.mockReturnValue(query({ items: [] }));
    mocks.campaignMetrics.mockReturnValue(query({ items: [] }));
    mocks.followUps.mockReturnValue(
      query({ items: [], total: 0, page: 1, page_size: 5 }),
    );
  });

  it("renders the six documented KPI cards", () => {
    render(<DashboardScreen />);
    expect(screen.getByText("Donors reached")).toBeVisible();
    expect(screen.getByText("Delivery rate")).toBeVisible();
    expect(screen.getByText("Read rate")).toBeVisible();
    expect(screen.getByText("Response rate")).toBeVisible();
    expect(screen.getByText("Confirmed")).toBeVisible();
    expect(screen.getByText("Needs call")).toBeVisible();
  });

  it("shows a retryable error when metrics cannot load", () => {
    mocks.overview.mockReturnValue({
      ...query(),
      error: new Error("network unavailable"),
    });
    render(<DashboardScreen />);
    expect(
      screen.getByText("Dashboard metrics could not be loaded."),
    ).toBeVisible();
  });
});
