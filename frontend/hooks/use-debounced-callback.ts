"use client";

import { useCallback, useEffect, useRef } from "react";

/** Delay callback execution and cancel pending work on unmount. */
export function useDebouncedCallback<TValue>(
  callback: (value: TValue) => void,
  delay: number,
): (value: TValue) => void {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    },
    [],
  );

  return useCallback(
    (value: TValue) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => callback(value), delay);
    },
    [callback, delay],
  );
}
