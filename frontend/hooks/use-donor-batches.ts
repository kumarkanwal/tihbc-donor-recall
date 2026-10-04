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

export type BatchPreview = components["schemas"]["BatchPreview"];
export type DonorBatch = components["schemas"]["DonorBatchOut"];
export type DonorBatchDetail = components["schemas"]["DonorBatchDetail"];
export type DonorBatchPage = components["schemas"]["DonorBatchPage"];
export type Donor = components["schemas"]["DonorOut"];
export type DonorPage = components["schemas"]["DonorPage"];
export type ValidationIssue = components["schemas"]["ValidationIssue"];
export type LanguageCode = components["schemas"]["LanguageCode"];

export type BatchListParameters = NonNullable<
  operations["list_batches_api_v1_donor_batches_get"]["parameters"]["query"]
>;
export type DonorListParameters = NonNullable<
  operations["list_batch_donors_api_v1_donor_batches__batch_id__donors_get"]["parameters"]["query"]
>;

export const donorBatchKeys = {
  all: ["donor-batches"] as const,
  list: (parameters: BatchListParameters) =>
    [...donorBatchKeys.all, "list", parameters] as const,
  detail: (batchId: string) =>
    [...donorBatchKeys.all, "detail", batchId] as const,
  donors: (batchId: string, parameters: DonorListParameters) =>
    [...donorBatchKeys.detail(batchId), "donors", parameters] as const,
  validation: (batchId: string) =>
    [...donorBatchKeys.detail(batchId), "validation"] as const,
};

/** Convert documented donor-batch failures into clear staff-facing copy. */
export function getDonorBatchErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!(error instanceof ApiError)) {
    return fallback;
  }

  if (error.code === "PREVIEW_EXPIRED") {
    return "This upload preview has expired. Upload the file again to continue.";
  }
  if (error.code === "FORBIDDEN") {
    return "Only administrators can upload and import donor batches.";
  }
  if (error.code === "UPLOAD_INVALID") {
    return `The file could not be uploaded. ${error.message}`;
  }
  if (error.code === "VALIDATION_ERROR") {
    return error.message;
  }
  return error.message || fallback;
}

/** Fetch the server-paginated donor batch list. */
export function useDonorBatches(
  parameters: BatchListParameters,
): UseQueryResult<DonorBatchPage> {
  return useQuery({
    queryKey: donorBatchKeys.list(parameters),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/donor-batches", {
        params: { query: parameters },
      });
      return requireResponseData(data, "Donor batch list");
    },
  });
}

/** Validate a donor file without importing it. */
export function usePreviewDonorBatch(): UseMutationResult<
  BatchPreview,
  Error,
  File
> {
  return useMutation({
    mutationFn: async (file) => {
      const { data } = await apiClient.POST("/api/v1/donor-batches/preview", {
        body: {
          // FastAPI's OpenAPI export omits the binary format, but openapi-fetch
          // still serializes the runtime File correctly as multipart data.
          file: file as unknown as string,
        },
      });
      return requireResponseData(data, "Batch preview");
    },
  });
}

interface ImportBatchVariables {
  name: string;
  previewToken: string;
}

/** Import the valid rows from a live preview token. */
export function useImportDonorBatch(): UseMutationResult<
  DonorBatch,
  Error,
  ImportBatchVariables
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name, previewToken }) => {
      const { data } = await apiClient.POST("/api/v1/donor-batches", {
        body: { name, preview_token: previewToken },
      });
      return requireResponseData(data, "Batch import");
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: donorBatchKeys.all });
    },
  });
}

/** Download the authenticated sample CSV as a browser Blob. */
export function useSampleBatchFile(): UseMutationResult<Blob, Error, void> {
  return useMutation({
    mutationFn: async () => {
      const result = await apiClient.GET("/api/v1/donor-batches/sample-file", {
        parseAs: "blob",
      });
      return requireResponseData(
        result.data as Blob | undefined,
        "Sample file",
      );
    },
  });
}

/** Fetch one donor batch summary. */
export function useDonorBatch(
  batchId: string,
): UseQueryResult<DonorBatchDetail> {
  return useQuery({
    queryKey: donorBatchKeys.detail(batchId),
    queryFn: async () => {
      const { data } = await apiClient.GET("/api/v1/donor-batches/{batch_id}", {
        params: { path: { batch_id: batchId } },
      });
      return requireResponseData(data, "Donor batch");
    },
  });
}

/** Fetch filtered donors belonging to one batch. */
export function useBatchDonors(
  batchId: string,
  parameters: DonorListParameters,
): UseQueryResult<DonorPage> {
  return useQuery({
    queryKey: donorBatchKeys.donors(batchId, parameters),
    queryFn: async () => {
      const { data } = await apiClient.GET(
        "/api/v1/donor-batches/{batch_id}/donors",
        {
          params: {
            path: { batch_id: batchId },
            query: parameters,
          },
        },
      );
      return requireResponseData(data, "Batch donors");
    },
  });
}

/** Fetch the persisted invalid-row report for one imported batch. */
export function useBatchValidationReport(
  batchId: string,
  enabled = true,
): UseQueryResult<ValidationIssue[]> {
  return useQuery({
    queryKey: donorBatchKeys.validation(batchId),
    queryFn: async () => {
      const { data } = await apiClient.GET(
        "/api/v1/donor-batches/{batch_id}/validation-report",
        { params: { path: { batch_id: batchId } } },
      );
      return requireResponseData(data, "Validation report");
    },
    enabled,
  });
}
