"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { clearSession } from "@/lib/api/session";
import { realtimeClient } from "@/lib/ws/client";

/** Clear all authenticated browser state and return to login. */
export function useLogout(): () => void {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useCallback(() => {
    realtimeClient.disconnect();
    clearSession();
    queryClient.clear();
    router.replace("/login");
  }, [queryClient, router]);
}
