"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { SessionUser } from "@/lib/auth/session-store";
import { useSessionStore } from "@/lib/auth/session-store";

export const currentUserQueryKey = ["auth", "current-user"] as const;

async function getCurrentUser(): Promise<SessionUser> {
  const { data } = await apiClient.GET("/api/v1/auth/me");

  if (!data) {
    throw new Error("The current-user response was empty.");
  }

  return data;
}

/** Return the server-confirmed current staff user. */
export function useCurrentUser(): UseQueryResult<SessionUser> {
  const token = useSessionStore((state) => state.token);

  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    enabled: Boolean(token),
  });
}
