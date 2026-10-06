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
import { uploadSeriesMediaFile } from "@/lib/api/uploads";

export type ContentSeries = components["schemas"]["ContentSeriesOut"];
export type ContentSeriesDetail = components["schemas"]["ContentSeriesDetail"];
export type ContentSeriesPage = components["schemas"]["ContentSeriesPage"];
export type ContentSeriesCreate = components["schemas"]["ContentSeriesCreate"];
export type ContentSeriesUpdate = components["schemas"]["ContentSeriesUpdate"];
export type SeriesStep = components["schemas"]["SeriesStepOut"];
export type SeriesStepInput = components["schemas"]["SeriesStepInput"];
export type SeriesStepUpdate = components["schemas"]["SeriesStepUpdate"];
export type SeriesPreview = components["schemas"]["SeriesPreviewMessage"];
export type SeriesLanguage = components["schemas"]["LanguageCode"];
export type SeriesKind = components["schemas"]["SeriesKind"];
export type SeriesStatus = components["schemas"]["SeriesStatus"];
export type MediaUpload = components["schemas"]["MediaUploadOut"];
export type SeriesListParameters = NonNullable<
  operations["list_content_series_api_v1_content_series_get"]["parameters"]["query"]
>;

export interface ActivationProblem {
  step: number | null;
  language: string | null;
  field: string;
  reason: string;
}

export const contentSeriesKeys = {
  all: ["content-series"] as const,
  list: (parameters: SeriesListParameters) =>
    [...contentSeriesKeys.all, "list", parameters] as const,
  detail: (seriesId: string) =>
    [...contentSeriesKeys.all, "detail", seriesId] as const,
  preview: (seriesId: string, stepId: string, language: SeriesLanguage) =>
    [
      ...contentSeriesKeys.detail(seriesId),
      "preview",
      stepId,
      language,
    ] as const,
};

async function invalidateSeries(
  queryClient: ReturnType<typeof useQueryClient>,
): Promise<void> {
  await queryClient.invalidateQueries({ queryKey: contentSeriesKeys.all });
}

/** Convert documented content-series failures into staff-facing copy. */
export function getContentSeriesErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!(error instanceof ApiError)) return fallback;
  if (error.code === "CONFLICT") {
    return `This series cannot be changed while it is used by an active campaign. ${error.message}`;
  }
  if (error.code === "VALIDATION_ERROR") return error.message;
  if (error.code === "FORBIDDEN")
    return "Only administrators can change content series.";
  return error.message || fallback;
}

/** Read structured activation problems from the shared error envelope. */
export function getActivationProblems(error: unknown): ActivationProblem[] {
  if (!(error instanceof ApiError) || !Array.isArray(error.details.problems))
    return [];
  return error.details.problems.filter((value): value is ActivationProblem => {
    if (!value || typeof value !== "object") return false;
    const item = value as Record<string, unknown>;
    return (
      (typeof item.step === "number" || item.step === null) &&
      typeof item.field === "string" &&
      typeof item.reason === "string" &&
      (typeof item.language === "string" || item.language === null)
    );
  });
}

export function useContentSeries(
  parameters: SeriesListParameters,
): UseQueryResult<ContentSeriesPage> {
  return useQuery({
    queryKey: contentSeriesKeys.list(parameters),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/content-series", {
        params: { query: parameters },
      });
      return requireResponseData(data, "Content series list");
    },
  });
}

export function useContentSeriesDetail(
  seriesId: string,
): UseQueryResult<ContentSeriesDetail> {
  return useQuery({
    queryKey: contentSeriesKeys.detail(seriesId),
    queryFn: async () => {
      const { data } = await apiClient.GET(
        "/api/v1/content-series/{series_id}",
        { params: { path: { series_id: seriesId } } },
      );
      return requireResponseData(data, "Content series");
    },
    enabled: Boolean(seriesId),
  });
}

export function useCreateContentSeries(): UseMutationResult<
  ContentSeriesDetail,
  Error,
  ContentSeriesCreate
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.POST("/api/v1/content-series", { body });
      return requireResponseData(data, "Content series create");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

function useSeriesAction(
  path:
    | "/api/v1/content-series/{series_id}/actions/activate"
    | "/api/v1/content-series/{series_id}/actions/archive"
    | "/api/v1/content-series/{series_id}/actions/duplicate",
): UseMutationResult<ContentSeriesDetail, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (seriesId) => {
      const parameters = { params: { path: { series_id: seriesId } } } as const;
      const data =
        path === "/api/v1/content-series/{series_id}/actions/activate"
          ? (
              await apiClient.POST(
                "/api/v1/content-series/{series_id}/actions/activate",
                parameters,
              )
            ).data
          : path === "/api/v1/content-series/{series_id}/actions/archive"
            ? (
                await apiClient.POST(
                  "/api/v1/content-series/{series_id}/actions/archive",
                  parameters,
                )
              ).data
            : (
                await apiClient.POST(
                  "/api/v1/content-series/{series_id}/actions/duplicate",
                  parameters,
                )
              ).data;
      return requireResponseData(data, "Content series action");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

export const useActivateContentSeries = () =>
  useSeriesAction("/api/v1/content-series/{series_id}/actions/activate");
export const useArchiveContentSeries = () =>
  useSeriesAction("/api/v1/content-series/{series_id}/actions/archive");
export const useDuplicateContentSeries = () =>
  useSeriesAction("/api/v1/content-series/{series_id}/actions/duplicate");

export function useUpdateContentSeries(
  seriesId: string,
): UseMutationResult<ContentSeriesDetail, Error, ContentSeriesUpdate> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.PATCH(
        "/api/v1/content-series/{series_id}",
        { params: { path: { series_id: seriesId } }, body },
      );
      return requireResponseData(data, "Content series update");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

export function useCreateSeriesStep(
  seriesId: string,
): UseMutationResult<SeriesStep, Error, SeriesStepInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.POST(
        "/api/v1/content-series/{series_id}/steps",
        { params: { path: { series_id: seriesId } }, body },
      );
      return requireResponseData(data, "Series step create");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

export function useUpdateSeriesStep(
  seriesId: string,
  stepId: string,
): UseMutationResult<SeriesStep, Error, SeriesStepUpdate> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await apiClient.PATCH(
        "/api/v1/content-series/{series_id}/steps/{step_id}",
        { params: { path: { series_id: seriesId, step_id: stepId } }, body },
      );
      return requireResponseData(data, "Series step update");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

export function useDeleteSeriesStep(
  seriesId: string,
): UseMutationResult<ContentSeriesDetail, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (stepId) => {
      const { data } = await apiClient.DELETE(
        "/api/v1/content-series/{series_id}/steps/{step_id}",
        { params: { path: { series_id: seriesId, step_id: stepId } } },
      );
      return requireResponseData(data, "Series step delete");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

export function useReorderSeriesSteps(
  seriesId: string,
): UseMutationResult<ContentSeriesDetail, Error, string[]> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (stepIds) => {
      const { data } = await apiClient.POST(
        "/api/v1/content-series/{series_id}/steps/actions/reorder",
        {
          params: { path: { series_id: seriesId } },
          body: { step_ids: stepIds },
        },
      );
      return requireResponseData(data, "Series step reorder");
    },
    onSuccess: async () => invalidateSeries(queryClient),
  });
}

export function useSeriesPreview(
  seriesId: string,
  stepId: string | null,
  language: SeriesLanguage,
): UseQueryResult<SeriesPreview> {
  return useQuery({
    queryKey: contentSeriesKeys.preview(seriesId, stepId ?? "", language),
    queryFn: async () => {
      const { data } = await apiClient.POST(
        "/api/v1/content-series/{series_id}/preview",
        {
          params: { path: { series_id: seriesId } },
          body: { step_id: stepId!, language },
        },
      );
      return requireResponseData(data, "Series preview");
    },
    enabled: Boolean(seriesId && stepId),
  });
}

export function useUploadSeriesMedia(): UseMutationResult<
  MediaUpload,
  Error,
  File
> {
  return useMutation({
    mutationFn: uploadSeriesMediaFile,
  });
}
