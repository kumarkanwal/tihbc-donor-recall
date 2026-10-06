"use client";

import { createContext, useContext } from "react";

/** Current authoritative demo time, supplied once by the dashboard shell. */
export const DemoTimeContext = createContext<Date | null>(null);

/** Read demo time without falling back to the browser wall clock. */
export function useDemoNow(): Date | null {
  return useContext(DemoTimeContext);
}
