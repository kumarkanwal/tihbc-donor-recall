"use client";

import type { ReactNode } from "react";

import { useDemoClock } from "@/hooks/use-demo-clock";
import { env } from "@/lib/env";
import { DemoTimeContext } from "@/lib/demo-time";

/** Share the authoritative demo time with all time-sensitive presentation UI. */
export function DemoTimeProvider({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  const clock = useDemoClock(env.NEXT_PUBLIC_DEMO_MODE);
  const value = clock.data ? new Date(clock.data.now) : null;

  return (
    <DemoTimeContext.Provider value={value}>
      {children}
    </DemoTimeContext.Provider>
  );
}
