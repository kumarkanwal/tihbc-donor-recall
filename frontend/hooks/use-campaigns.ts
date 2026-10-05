"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { requireResponseData } from "@/lib/api/response";
import type { components, operations } from "@/lib/api/schema";

export type Campaign = components["schemas"]["CampaignOut"];
export type CampaignDetail = components["schemas"]["CampaignDetail"];
export type CampaignPage = components["schemas"]["CampaignPage"];
export type CampaignCreate = components["schemas"]["CampaignCreate"];
export type CampaignUpdate = components["schemas"]["CampaignUpdate"];
export type CampaignStatus = components["schemas"]["CampaignStatus"];
export type Enrollment = components["schemas"]["EnrollmentOut"];
export type EnrollmentDetail = components["schemas"]["EnrollmentDetail"];
export type EnrollmentPage = components["schemas"]["EnrollmentPage"];
export type EnrollmentStatus = components["schemas"]["EnrollmentStatus"];
export type CampaignListParameters = NonNullable<
  operations["list_campaigns_api_v1_campaigns_get"]["parameters"]["query"]
>;
export type EnrollmentListParameters = NonNullable<
  operations["list_campaign_enrollments_api_v1_campaigns__campaign_id__enrollments_get"]["parameters"]["query"]
>;

export interface CampaignLaunchProblem {
  field: string;
  reason: string;
}

export const campaignKeys = {
  all: ["campaigns"] as const,
  list: (parameters: CampaignListParameters) =>
    [...campaignKeys.all, "list", parameters] as const,
  catalog: (status: CampaignStatus | undefined) =>
    [...campaignKeys.all, "catalog", status ?? "all"] as const,
  detail: (campaignId: string) =>
    [...campaignKeys.all, "detail", campaignId] as const,
  enrollments: (campaignId: string, parameters: EnrollmentListParameters) =>
    [...campaignKeys.detail(campaignId), "enrollments", parameters] as const,
  enrollment: (enrollmentId: string) => ["enrollments", enrollmentId] as const,
};

/** Convert documented campaign failures into clear staff-facing copy. */
export function getCampaignErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!(error instanceof ApiError)) return fallback;
  if (error.code === "FORBIDDEN") {
    return "Only administrators can change campaign settings or status.";
  }
  if (error.code === "INVALID_STATE_TRANSITION") {
    return `This action is not available for the campaign's current status. ${error.message}`;
  }
  if (error.code === "CONFLICT") {
    return `The campaign conflicts with another active workflow. ${error.message}`;
  }
  return error.message || fallback;
}

/** Read aggregate launch problems from the standard API error envelope. */
export function getCampaignLaunchProblems(
  error: unknown,
): CampaignLaunchProblem[] {
  if (!(error instanceof ApiError) || !Array.isArray(error.details.problems)) {
    return [];
  }
  return error.details.problems.filter(
    (value): value is CampaignLaunchProblem => {
      if (!value || typeof value !== "object") return false;
      const item = value as Record<string, unknown>;
      return typeof item.field === "string" && typeof item.reason === "string";
    },
  );
}

async function invalidateCampaigns(
  queryClient: ReturnType<typeof useQueryClient>,
): Promise<void> {
  await queryClient.invalidateQueries({ queryKey: campaignKeys.all });
}

export function useCampaigns(
  parameters: CampaignListParameters,
): UseQueryResult<CampaignPage> {
  return useQuery({
    queryKey: campaignKeys.list(parameters),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/campaigns", {
        params: { query: parameters },
      });
      return requireResponseData(data, "Campaign list");
    },
  });
}

/** Load the complete status-filtered catalog for client-side search and sort. */
export function useCampaignCatalog(
  status?: CampaignStatus,
): UseQueryResult<CampaignPage> {
  return useQuery({
    queryKey: campaignKeys.catalog(status),
    queryFn: async () => {
      const pageSize = 100;
      const loadPage = async (page: number): Promise<CampaignPage> => {
        const { data } = await apiClient.GET("/api/v1/campaigns", {
          params: { query: { status, page, page_size: pageSize } },
        });
        return requireResponseData(data, "Campaign list");
      };
      const first = await loadPage(1);
      const items = [...first.items];
      for (let page = 2; items.length < first.total; page += 1) {
        const next = await loadPage(page);
        if (next.items.length === 0) {
          throw new Error("Campaign list pagination ended before its total.");
        }
        items.push(...next.items);
      }
      return { ...first, items, page: 1, page_size: items.length || pageSize };
    },
  });
}

export function useCampaign(
  campaignId: string,
): UseQueryResult<CampaignDetail> {
  return useQuery({
    queryKey: campaignKeys.detail(campaignId),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/campaigns/{campaign_id}", {
        params: { path: { campaign_id: campaignId } },
      });
      return requireResponseData(data, "Campaign");
    },
    enabled: Boolean(campaignId),
  });
}

export function useCreateCampaign(): UseMutationResult<
  CampaignDetail,
  Error,
  CampaignCreate
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.POST("/api/v1/campaigns", { body });
      return requireResponseData(data, "Campaign create");
    },
    onSuccess: async () => invalidateCampaigns(queryClient),
  });
}

export function useUpdateCampaign(
  campaignId: string,
): UseMutationResult<CampaignDetail, Error, CampaignUpdate> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.PATCH(
        "/api/v1/campaigns/{campaign_id}",
        { params: { path: { campaign_id: campaignId } }, body },
      );
      return requireResponseData(data, "Campaign update");
    },
    onSuccess: async () => invalidateCampaigns(queryClient),
  });
}

function useCampaignAction(
  action: "launch" | "pause" | "resume",
): UseMutationResult<CampaignDetail, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (campaignId) => {
      const parameters = {
        params: { path: { campaign_id: campaignId } },
      } as const;
      const data =
        action === "launch"
          ? (
              await apiClient.POST(
                "/api/v1/campaigns/{campaign_id}/actions/launch",
                parameters,
              )
            ).data
          : action === "pause"
            ? (
                await apiClient.POST(
                  "/api/v1/campaigns/{campaign_id}/actions/pause",
                  parameters,
                )
              ).data
            : (
                await apiClient.POST(
                  "/api/v1/campaigns/{campaign_id}/actions/resume",
                  parameters,
                )
              ).data;
      return requireResponseData(data, `Campaign ${action}`);
    },
    onSuccess: async () => invalidateCampaigns(queryClient),
  });
}

export const useLaunchCampaign = () => useCampaignAction("launch");
export const usePauseCampaign = () => useCampaignAction("pause");
export const useResumeCampaign = () => useCampaignAction("resume");

export function useCampaignEnrollments(
  campaignId: string,
  parameters: EnrollmentListParameters,
): UseQueryResult<EnrollmentPage> {
  return useQuery({
    queryKey: campaignKeys.enrollments(campaignId, parameters),
    queryFn: async () => {
      const { data } = await apiClient.GET(
        "/api/v1/campaigns/{campaign_id}/enrollments",
        { params: { path: { campaign_id: campaignId }, query: parameters } },
      );
      return requireResponseData(data, "Campaign enrollments");
    },
    enabled: Boolean(campaignId),
  });
}

export function useEnrollment(
  enrollmentId: string | null,
): UseQueryResult<EnrollmentDetail> {
  return useQuery({
    queryKey: campaignKeys.enrollment(enrollmentId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.GET(
        "/api/v1/enrollments/{enrollment_id}",
        {
          params: { path: { enrollment_id: enrollmentId! } },
        },
      );
      return requireResponseData(data, "Enrollment");
    },
    enabled: Boolean(enrollmentId),
  });
}
