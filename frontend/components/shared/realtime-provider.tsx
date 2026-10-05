"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo } from "react";

import { useSessionStore } from "@/lib/auth/session-store";
import { env } from "@/lib/env";
import { simulatorSource } from "@/lib/simulator";
import { showToast } from "@/lib/toast/store";
import { realtimeClient } from "@/lib/ws/client";
import { createEventRouter } from "@/lib/ws/event-router";

/** Bind the single tab-scoped socket and mock simulator events to Query cache. */
export function RealtimeProvider({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  const queryClient = useQueryClient();
  const token = useSessionStore((state) => state.token);
  const eventRouter = useMemo(
    () => createEventRouter(queryClient, { toast: showToast }),
    [queryClient],
  );

  useEffect(() => {
    const unsubscribe = realtimeClient.subscribe(eventRouter.route);
    const stopReconnect = realtimeClient.onReconnect(() => {
      void queryClient.refetchQueries({ type: "active" });
    });
    return () => {
      unsubscribe();
      stopReconnect();
      eventRouter.dispose();
    };
  }, [eventRouter, queryClient]);

  useEffect(() => {
    if (env.NEXT_PUBLIC_REALTIME && token) realtimeClient.connect(token);
    else realtimeClient.disconnect();
    return () => realtimeClient.disconnect();
  }, [token]);

  useEffect(() => {
    if (env.NEXT_PUBLIC_SIMULATOR_SOURCE !== "mock") return;
    return simulatorSource.subscribe((event) =>
      eventRouter.route({ ...event, ts: new Date().toISOString() }),
    );
  }, [eventRouter]);

  return <>{children}</>;
}
