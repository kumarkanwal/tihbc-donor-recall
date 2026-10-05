import { QueryClient } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { simulatorKeys } from "@/lib/simulator/query-keys";

import { clockQueryKey, createEventRouter } from "./event-router";
import type { RealtimeEvent } from "./events";

const timestamp = "2026-10-04T10:00:00Z";

describe("realtime event router", () => {
  afterEach(() => vi.useRealTimers());

  it("maps simulator, campaign, clock, and debounced metrics events", () => {
    vi.useFakeTimers();
    const queryClient = new QueryClient();
    const invalidate = vi
      .spyOn(queryClient, "invalidateQueries")
      .mockResolvedValue();
    const router = createEventRouter(queryClient, { toast: vi.fn() });

    router.route({
      type: "message.status_updated",
      ts: timestamp,
      payload: {
        id: "message-1",
        donor_id: "donor-1",
        status: "read",
        delivered_at: timestamp,
        read_at: timestamp,
        failed_reason: null,
      },
    });
    router.route({
      type: "campaign.updated",
      ts: timestamp,
      payload: { id: "campaign-1", status: "running", counts: {} },
    });
    router.route({
      type: "clock.updated",
      ts: timestamp,
      payload: { now: timestamp, offset_seconds: 3_600 },
    });
    router.route({
      type: "metrics.updated",
      ts: timestamp,
      payload: { campaign_id: "campaign-1" },
    });

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: simulatorKeys.messages("donor-1"),
    });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["campaigns"] });
    expect(queryClient.getQueryData(clockQueryKey)).toEqual({
      now: timestamp,
      offset_seconds: 3_600,
    });
    expect(invalidate).not.toHaveBeenCalledWith({ queryKey: ["metrics"] });
    vi.advanceTimersByTime(2_000);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["metrics"] });
    router.dispose();
  });

  it("shows a toast and refreshes follow-ups when one is created", () => {
    const queryClient = new QueryClient();
    const invalidate = vi
      .spyOn(queryClient, "invalidateQueries")
      .mockResolvedValue();
    const toast = vi.fn();
    const router = createEventRouter(queryClient, { toast });
    const event: RealtimeEvent = {
      type: "followup.created",
      ts: timestamp,
      payload: {
        id: "follow-up-1",
        enrollment_id: "enrollment-1",
        type: "needs_call",
        status: "open",
        priority: "high",
        assigned_to_id: null,
        created_at: timestamp,
        updated_at: timestamp,
      },
    };
    router.route(event);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["follow-ups"] });
    expect(toast).toHaveBeenCalledWith(
      "New follow-up",
      "A donor needs coordinator attention.",
    );
    router.dispose();
  });
});
