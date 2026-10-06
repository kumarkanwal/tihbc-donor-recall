import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api/client";

import { previewDonorBatchFile, uploadSeriesMediaFile } from "./uploads";

vi.mock("@/lib/env", () => ({
  env: { NEXT_PUBLIC_API_URL: "http://localhost:8000/api/v1" },
}));

describe("multipart uploads", () => {
  afterEach(() => vi.restoreAllMocks());

  it("sends batch and media files as FormData under the file field", async () => {
    const post = vi
      .spyOn(apiClient, "POST")
      .mockResolvedValueOnce({
        data: { preview_token: "preview-token" },
        response: new Response(null, { status: 200 }),
      } as never)
      .mockResolvedValueOnce({
        data: { url: "/media/image.png", media_type: "image" },
        response: new Response(null, { status: 201 }),
      } as never);
    const batchFile = new File(["name,phone"], "donors.csv", {
      type: "text/csv",
    });
    const mediaFile = new File(["image"], "image.png", {
      type: "image/png",
    });

    await previewDonorBatchFile(batchFile);
    await uploadSeriesMediaFile(mediaFile);

    const calls = post.mock.calls as unknown as Array<
      [string, { body?: unknown; headers?: unknown }]
    >;
    const batchOptions = calls[0]?.[1];
    const mediaOptions = calls[1]?.[1];
    expect(batchOptions?.body).toBeInstanceOf(FormData);
    expect((batchOptions?.body as unknown as FormData).get("file")).toBe(
      batchFile,
    );
    expect(batchOptions).not.toHaveProperty("headers");
    expect(mediaOptions?.body).toBeInstanceOf(FormData);
    expect((mediaOptions?.body as unknown as FormData).get("file")).toBe(
      mediaFile,
    );
    expect(mediaOptions).not.toHaveProperty("headers");
  });
});
