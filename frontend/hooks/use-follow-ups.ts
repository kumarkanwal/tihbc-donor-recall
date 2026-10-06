"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  type FollowUpDetail,
  type FollowUpFilters,
  type FollowUpOutcome,
  type FollowUpPage,
  type FollowUpStatus,
  type FollowUpSummary,
} from "@/lib/api/contracts";
import { apiClient } from "@/lib/api/client";
import { requireResponseData } from "@/lib/api/response";
import { downloadBlob } from "@/lib/utils/download";

export const followUpKeys = {
  all: ["follow-ups"] as const,
  list: (filters: FollowUpFilters) => ["follow-ups", "list", filters] as const,
  summary: (filters: FollowUpFilters) =>
    ["follow-ups", "summary", filters] as const,
  detail: (id: string) => ["follow-ups", "detail", id] as const,
};

export function useFollowUps(
  filters: FollowUpFilters,
): UseQueryResult<FollowUpPage> {
  return useQuery({
    queryKey: followUpKeys.list(filters),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/follow-ups", {
        params: { query: filters },
      });
      return requireResponseData(data, "Follow-up list");
    },
  });
}

export function useFollowUpSummary(
  filters: FollowUpFilters,
): UseQueryResult<FollowUpSummary> {
  return useQuery({
    queryKey: followUpKeys.summary(filters),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/follow-ups/summary", {
        params: { query: filters },
      });
      return requireResponseData(data, "Follow-up summary");
    },
  });
}

export function useFollowUp(id: string | null): UseQueryResult<FollowUpDetail> {
  return useQuery({
    queryKey: followUpKeys.detail(id ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/follow-ups/{item_id}", {
        params: { path: { item_id: id ?? "" } },
      });
      return requireResponseData(data, "Follow-up detail");
    },
    enabled: Boolean(id),
  });
}

type FollowUpPatch = {
  status?: FollowUpStatus;
  assigned_to_id?: string;
  priority?: "normal" | "high";
};

export function useUpdateFollowUp(
  id: string,
): UseMutationResult<FollowUpDetail, Error, FollowUpPatch> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.PATCH("/api/v1/follow-ups/{item_id}", {
        params: { path: { item_id: id } },
        body,
      });
      return requireResponseData(data, "Updated follow-up");
    },
    onSuccess: async (detail) => {
      queryClient.setQueryData(followUpKeys.detail(id), detail);
      await queryClient.invalidateQueries({ queryKey: followUpKeys.all });
    },
  });
}

export function useAddFollowUpNote(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (note: string) => {
      const { data } = await apiClient.POST(
        "/api/v1/follow-ups/{item_id}/notes",
        { params: { path: { item_id: id } }, body: { note } },
      );
      return requireResponseData(data, "Follow-up note");
    },
    onSuccess: async (detail) => {
      queryClient.setQueryData(followUpKeys.detail(id), detail);
      await queryClient.invalidateQueries({ queryKey: followUpKeys.all });
    },
  });
}

export function useResolveFollowUp(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { outcome: FollowUpOutcome; note?: string }) => {
      const { data } = await apiClient.POST(
        "/api/v1/follow-ups/{item_id}/actions/resolve",
        { params: { path: { item_id: id } }, body: input },
      );
      return requireResponseData(data, "Resolved follow-up");
    },
    onSuccess: async (detail) => {
      queryClient.setQueryData(followUpKeys.detail(id), detail);
      await queryClient.invalidateQueries({ queryKey: followUpKeys.all });
    },
  });
}

export function useExportFollowUps(filters: FollowUpFilters) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.GET("/api/v1/follow-ups/export", {
        params: { query: filters },
        parseAs: "blob",
      });
      return requireResponseData(data, "Follow-up export");
    },
    onSuccess: (blob) => downloadBlob(blob, "tihbc-follow-ups.csv"),
  });
}
