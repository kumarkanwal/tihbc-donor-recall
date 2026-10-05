import { QueryClient } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api/client";

import {
  advanceDemoClock,
  invalidateAfterClockChange,
  resetDemoClock,
} from "./use-demo-clock";

vi.mock("@/lib/env", () => ({
  env: {
    NEXT_PUBLIC_API_URL: "http://localhost:8000/api/v1",
    NEXT_PUBLIC_WS_URL: "ws://localhost:8000/ws",
    NEXT_PUBLIC_DEMO_MODE: true,
    NEXT_PUBLIC_SIMULATOR_SOURCE: "mock",
    NEXT_PUBLIC_REALTIME: false,
  },
}));

const clock = {
  now: "2026-10-05T10:00:00Z",
  offset_seconds: 86_400,
};

describe("demo clock actions", () => {
  afterEach(() => vi.restoreAllMocks());

  it("calls advance and reset with the documented API shapes", async () => {
    const post = vi.spyOn(apiClient, "POST").mockResolvedValue({
      data: clock,
      response: new Response(null, { status: 200 }),
    } as never);

    await expect(advanceDemoClock({ days: 1, hours: 0 })).resolves.toEqual(
      clock,
    );
    expect(post).toHaveBeenNthCalledWith(
      1,
      "/api/v1/demo/clock/actions/advance",
      { body: { days: 1, hours: 0 } },
    );
    await expect(resetDemoClock()).resolves.toEqual(clock);
    expect(post).toHaveBeenNthCalledWith(2, "/api/v1/demo/clock/actions/reset");
  });

  it("invalidates all time-sensitive query domains", async () => {
    const queryClient = new QueryClient();
    const invalidate = vi
      .spyOn(queryClient, "invalidateQueries")
      .mockResolvedValue();
    await invalidateAfterClockChange(queryClient);
    expect(
      invalidate.mock.calls.map(([filters]) => filters?.queryKey),
    ).toEqual([
      ["campaigns"],
      ["enrollments"],
      ["simulator"],
      ["metrics"],
    ]);
  });
});
