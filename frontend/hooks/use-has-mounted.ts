"use client";

import { useSyncExternalStore } from "react";

const subscribeToHydration = (): (() => void) => () => undefined;

/** Report client hydration without effect-driven state updates. */
export function useHasMounted(): boolean {
  return useSyncExternalStore(
    subscribeToHydration,
    () => true,
    () => false,
  );
}
