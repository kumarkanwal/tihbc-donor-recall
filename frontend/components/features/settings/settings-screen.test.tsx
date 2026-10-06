import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsScreen } from "./settings-screen";

const mocks = vi.hoisted(() => ({
  isAdmin: true,
  integration: vi.fn(),
  users: vi.fn(),
  resetData: vi.fn(),
  advance: vi.fn(),
  resetClock: vi.fn(),
}));

vi.mock("@/hooks/use-can", () => ({ useCan: () => mocks.isAdmin }));
vi.mock("@/lib/env", () => ({ env: { NEXT_PUBLIC_DEMO_MODE: true } }));
vi.mock("@/hooks/use-settings", () => ({
  useIntegrationSettings: mocks.integration,
  useStaffUsers: mocks.users,
  useResetDemoData: () => ({
    mutate: mocks.resetData,
    isPending: false,
    error: null,
  }),
}));
vi.mock("@/hooks/use-demo-clock", () => ({
  formatDemoClock: () => "5 Oct 2026, 2:00 PM",
  useDemoClock: () => ({
    data: { now: "2026-10-05T09:00:00Z", offset_seconds: 0 },
    isPending: false,
    error: null,
  }),
  useAdvanceDemoClock: () => ({
    mutate: mocks.advance,
    isPending: false,
  }),
  useResetDemoClock: () => ({
    mutate: mocks.resetClock,
    isPending: false,
  }),
}));

describe("SettingsScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.isAdmin = true;
    mocks.integration.mockReturnValue({
      data: {
        business_verified: true,
        phone_number: "+92 300 1234567",
        display_name: "TIHBC",
        quality_rating: "High",
        messaging_limit: "1,000 per day",
        templates: [
          { name: "donor_recall_en", category: "utility", status: "approved" },
        ],
      },
      isPending: false,
      error: null,
      refetch: vi.fn(),
    });
    mocks.users.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isPending: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("shows the mocked integration status and templates", () => {
    render(<SettingsScreen />);
    expect(screen.getByText("Demo environment")).toBeVisible();
    expect(screen.getByText("Verified")).toBeVisible();
    expect(screen.getByText("donor_recall_en")).toBeVisible();
  });

  it("hides administrator demo controls from coordinators", () => {
    mocks.isAdmin = false;
    render(<SettingsScreen />);
    expect(
      screen.queryByRole("tab", { name: "Demo controls" }),
    ).not.toBeInTheDocument();
  });

  it("confirms a demo data reset for administrators", async () => {
    const user = userEvent.setup();
    render(<SettingsScreen />);
    await user.click(screen.getByRole("tab", { name: "Demo controls" }));
    await user.click(screen.getByRole("button", { name: "Reset demo data" }));
    const resetButtons = screen.getAllByRole("button", {
      name: "Reset demo data",
    });
    await user.click(resetButtons.at(-1)!);
    expect(mocks.resetData).toHaveBeenCalledOnce();
  });

  it("shows a retryable error when integration settings cannot load", () => {
    mocks.integration.mockReturnValue({
      data: undefined,
      isPending: false,
      error: new Error("network unavailable"),
      refetch: vi.fn(),
    });
    render(<SettingsScreen />);
    expect(
      screen.getByText("Integration settings could not be loaded."),
    ).toBeVisible();
  });
});
