import { apiClient } from "@/lib/api/client";
import { requireResponseData } from "@/lib/api/response";
import type { components } from "@/lib/api/schema";

type BatchPreview = components["schemas"]["BatchPreview"];
type BatchPreviewBody =
  components["schemas"]["Body_preview_batch_api_v1_donor_batches_preview_post"];
type MediaUpload = components["schemas"]["MediaUploadOut"];
type MediaUploadBody =
  components["schemas"]["Body_upload_media_api_v1_media_post"];

function createFileFormData(file: File): FormData {
  const body = new FormData();
  body.append("file", file);
  return body;
}

/** Validate a donor file through the generated multipart endpoint. */
export async function previewDonorBatchFile(file: File): Promise<BatchPreview> {
  const body = createFileFormData(file);
  const { data } = await apiClient.POST("/api/v1/donor-batches/preview", {
    // The generated schema exposes OpenAPI binary values as strings, while the
    // browser request must remain FormData so openapi-fetch preserves its boundary.
    body: body as unknown as BatchPreviewBody,
  });
  return requireResponseData(data, "Batch preview");
}

/** Upload series media through the generated multipart endpoint. */
export async function uploadSeriesMediaFile(file: File): Promise<MediaUpload> {
  const body = createFileFormData(file);
  const { data } = await apiClient.POST("/api/v1/media", {
    body: body as unknown as MediaUploadBody,
  });
  return requireResponseData(data, "Media upload");
}
