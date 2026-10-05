import type { QueryClient } from "@tanstack/react-query";

import { simulatorKeys } from "@/lib/simulator/query-keys";

import type { RealtimeEvent } from "./events";

const METRICS_DEBOUNCE_MS = 2_000;
export const clockQueryKey = ["demo-clock"] as const;

interface EventRouterOptions {
  toast: (title: string, description?: string) => void;
  setTimer?: typeof setTimeout;
  clearTimer?: typeof clearTimeout;
}

/** Centralize every realtime event's cache and notification effects. */
export function createEventRouter(
  queryClient: QueryClient,
  options: EventRouterOptions,
): { route: (event: RealtimeEvent) => void; dispose: () => void } {
  const setTimer = options.setTimer ?? setTimeout;
  const clearTimer = options.clearTimer ?? clearTimeout;
  let metricsTimer: ReturnType<typeof setTimeout> | null = null;

  function invalidateSimulator(donorId: string): void {
    void queryClient.invalidateQueries({
      queryKey: simulatorKeys.messages(donorId),
    });
    void queryClient.invalidateQueries({
      queryKey: simulatorKeys.conversations,
    });
  }

  function route(event: RealtimeEvent): void {
    switch (event.type) {
      case "message.created":
      case "message.status_updated":
        invalidateSimulator(event.payload.donor_id);
        break;
      case "simulator.typing":
        queryClient.setQueryData(
          simulatorKeys.typing(event.payload.donor_id),
          event.payload.is_typing,
        );
        break;
      case "enrollment.updated":
      case "campaign.updated":
        void queryClient.invalidateQueries({ queryKey: ["campaigns"] });
        void queryClient.invalidateQueries({ queryKey: ["enrollments"] });
        break;
      case "followup.created":
        void queryClient.invalidateQueries({ queryKey: ["follow-ups"] });
        options.toast("New follow-up", "A donor needs coordinator attention.");
        break;
      case "followup.updated":
        void queryClient.invalidateQueries({ queryKey: ["follow-ups"] });
        break;
      case "metrics.updated":
        if (metricsTimer) clearTimer(metricsTimer);
        metricsTimer = setTimer(() => {
          metricsTimer = null;
          void queryClient.invalidateQueries({ queryKey: ["metrics"] });
        }, METRICS_DEBOUNCE_MS);
        break;
      case "clock.updated":
        queryClient.setQueryData(clockQueryKey, event.payload);
        break;
    }
  }

  return {
    route,
    dispose: () => {
      if (metricsTimer) clearTimer(metricsTimer);
      metricsTimer = null;
    },
  };
}
