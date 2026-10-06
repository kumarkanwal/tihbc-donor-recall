import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DemoClockControl } from "./demo-clock-control";

const mocks = vi.hoisted(() => ({
  canManage: vi.fn(),
  advance: vi.fn(),
  reset: vi.fn(),
}));

vi.mock("@/hooks/use-can", () => ({ useCan: mocks.canManage }));
vi.mock("@/lib/env", () => ({
  env: { NEXT_PUBLIC_DEMO_MODE: true },
}));
vi.mock("@/hooks/use-demo-clock", () => ({
  formatDemoClock: () => "5 Oct 2026, 3:00 pm",
  useDemoClock: () => ({
    data: { now: "2026-10-05T10:00:00Z", offset_seconds: 0 },
    error: null,
    isPending: false,
  }),
  useAdvanceDemoClock: () => ({ isPending: false, mutate: mocks.advance }),
  useResetDemoClock: () => ({ isPending: false, mutate: mocks.reset }),
}));

describe("DemoClockControl", () => {
  beforeEach(() => vi.clearAllMocks());

  it("is hidden for coordinators", () => {
    mocks.canManage.mockReturnValue(false);
    render(<DemoClockControl />);
    expect(
      screen.queryByRole("button", { name: /Skip time/i }),
    ).not.toBeInTheDocument();
  });

  it("offers every skip option to administrators", async () => {
    mocks.canManage.mockReturnValue(true);
    const user = userEvent.setup();
    render(<DemoClockControl />);
    expect(screen.getByText("5 Oct 2026, 3:00 pm")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Skip time/i }));
    expect(screen.getByRole("menuitem", { name: "+1 hour" })).toBeVisible();
    expect(screen.getByRole("menuitem", { name: "+7 days" })).toBeVisible();
    await user.click(screen.getByRole("menuitem", { name: "+1 day" }));
    expect(mocks.advance).toHaveBeenCalledWith({ days: 1, hours: 0 });
  });
});
