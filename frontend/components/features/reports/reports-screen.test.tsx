import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MetricsOverview } from "@/lib/api/pending-contracts";

import { ReportsScreen } from "./reports-screen";

const mocks = vi.hoisted(() => ({
  overview: vi.fn(),
  campaignMetrics: vi.fn(),
  breakdown: vi.fn(),
  declineReasons: vi.fn(),
  inactive: vi.fn(),
  exportReport: vi.fn(),
  exportAction: vi.fn(),
  backend404: new Error("backend-404"),
}));

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
    children,
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  CartesianGrid: () => null,
  Bar: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));
vi.mock("@/hooks/use-campaigns", () => ({
  useCampaignCatalog: () => ({ data: { items: [] } }),
}));
vi.mock("@/hooks/use-metrics", () => ({
  useMetricsOverview: mocks.overview,
  useCampaignMetrics: mocks.campaignMetrics,
  useMetricsResponseBreakdown: mocks.breakdown,
  useDeclineReasons: mocks.declineReasons,
  useInactiveNumbers: mocks.inactive,
  useExportReport: mocks.exportReport,
}));
vi.mock("@/lib/api/pending-contracts", () => ({
  isPendingBackendUpdate: (error: unknown) => error === mocks.backend404,
}));

const overview: MetricsOverview = {
  donors: 10,
  sent: 10,
  delivered: 9,
  read: 8,
  responded: 4,
  delivery_rate: 90,
  read_rate: 80,
  response_rate: 40,
  confirmed: 2,
  rescheduled: 1,
  declined: 1,
  escalated: 1,
  invalid_numbers: 1,
  undeliverable: 1,
};

function query(data: unknown = undefined) {
  return { data, isPending: false, error: null, refetch: vi.fn() };
}

describe("ReportsScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.overview.mockReturnValue(query(overview));
    mocks.campaignMetrics.mockReturnValue(query({ items: [] }));
    mocks.breakdown.mockReturnValue(
      query({
        by_intent: { confirm: 2 },
        by_segment: { regular: 2 },
        by_language: { en: 2 },
      }),
    );
    mocks.declineReasons.mockReturnValue(query({ items: [] }));
    mocks.inactive.mockReturnValue(
      query({
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        summary: { invalid: 1, undeliverable: 1, total: 2 },
      }),
    );
    mocks.exportReport.mockReturnValue({
      mutate: mocks.exportAction,
      isPending: false,
      error: null,
    });
  });

  it("switches report tabs and targets the matching CSV export", async () => {
    const user = userEvent.setup();
    render(<ReportsScreen />);
    expect(screen.getByText("Campaign comparison")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Responses" }));
    expect(screen.getByText("Responses by intent")).toBeVisible();
    expect(mocks.exportReport).toHaveBeenLastCalledWith(
      "response-breakdown",
      expect.any(Object),
    );
    await user.click(screen.getByRole("button", { name: "Export CSV" }));
    expect(mocks.exportAction).toHaveBeenCalledOnce();

    await user.click(screen.getByRole("tab", { name: "Inactive numbers" }));
    expect(screen.getByText("Total inactive")).toBeVisible();
    expect(mocks.exportReport).toHaveBeenLastCalledWith(
      "inactive-numbers",
      expect.any(Object),
    );
  });

  it("shows the backend-update state for missing report endpoints", () => {
    mocks.overview.mockReturnValue({ ...query(), error: mocks.backend404 });
    render(<ReportsScreen />);
    expect(screen.getByText("Available after backend update")).toBeVisible();
  });
});
