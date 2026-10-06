"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { DemoClock, DemoClockAdvance } from "@/lib/api/contracts";
import { requireResponseData } from "@/lib/api/response";
import { showToast } from "@/lib/toast/store";
import { clockQueryKey } from "@/lib/ws/event-router";

export async function invalidateAfterClockChange(
  queryClient: QueryClient,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
    queryClient.invalidateQueries({ queryKey: ["enrollments"] }),
    queryClient.invalidateQueries({ queryKey: ["simulator"] }),
    queryClient.invalidateQueries({ queryKey: ["metrics"] }),
  ]);
}

export async function advanceDemoClock(
  input: DemoClockAdvance,
): Promise<DemoClock> {
  const { data } = await apiClient.POST("/api/v1/demo/clock/actions/advance", {
    body: input,
  });
  return requireResponseData(data, "Advanced demo clock");
}

export async function resetDemoClock(): Promise<DemoClock> {
  const { data } = await apiClient.POST("/api/v1/demo/clock/actions/reset");
  return requireResponseData(data, "Reset demo clock");
}

function useClockMutation<Variables>(
  mutation: (input: Variables) => Promise<DemoClock>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: mutation,
    onSuccess: async (clock) => {
      queryClient.setQueryData(clockQueryKey, clock);
      await invalidateAfterClockChange(queryClient);
      showToast("Demo time updated", formatDemoClock(clock.now));
    },
  });
}

/** Read the current demo clock when its role-gated control is eligible. */
export function useDemoClock(enabled = true) {
  return useQuery({
    queryKey: clockQueryKey,
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/demo/clock");
      return requireResponseData(data, "Demo clock");
    },
    enabled,
  });
}

/** Advance the demo clock and refresh every time-sensitive domain. */
export function useAdvanceDemoClock() {
  return useClockMutation(advanceDemoClock);
}

/** Reset the demo clock and refresh every time-sensitive domain. */
export function useResetDemoClock() {
  return useClockMutation<void>(resetDemoClock);
}

export function formatDemoClock(value: string): string {
  return new Intl.DateTimeFormat("en-PK", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Karachi",
  }).format(new Date(value));
}
