"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { IntegrationSettings } from "@/lib/api/contracts";
import { requireResponseData } from "@/lib/api/response";
import type { components } from "@/lib/api/schema";
import { showToast } from "@/lib/toast/store";

export type StaffUser = components["schemas"]["UserOut"];
export type StaffUserPage = components["schemas"]["UserPage"];

export const settingsKeys = {
  all: ["settings"] as const,
  integration: ["settings", "integration"] as const,
  users: (page: number, pageSize: number) =>
    ["settings", "users", page, pageSize] as const,
};

/** Load the mocked integration status from the documented settings endpoint. */
export function useIntegrationSettings(): UseQueryResult<IntegrationSettings> {
  return useQuery({
    queryKey: settingsKeys.integration,
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/settings/integration");
      return requireResponseData(data, "Integration settings");
    },
  });
}

/** Load one read-only page of active staff users. */
export function useStaffUsers(
  page: number,
  pageSize: number,
): UseQueryResult<StaffUserPage> {
  return useQuery({
    queryKey: settingsKeys.users(page, pageSize),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/users", {
        params: { query: { page, page_size: pageSize } },
      });
      return requireResponseData(data, "Staff users");
    },
  });
}

/** Reset seeded demo data and refresh all server-backed screens. */
export function useResetDemoData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.POST("/api/v1/demo/actions/reset-data");
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      showToast("Demo data reset", "The seeded demo data is ready to use.");
    },
  });
}
