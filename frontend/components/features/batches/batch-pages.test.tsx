import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BatchListScreen } from "@/components/features/batches/batch-list-screen";
import {
  ConfirmStep,
  ReviewStep,
} from "@/components/features/batches/batch-upload-steps";
import { BatchUploadWizard } from "@/components/features/batches/batch-upload-wizard";
import type { BatchPreview, DonorBatch } from "@/hooks/use-donor-batches";
import { ApiError } from "@/lib/api/errors";

const mocks = vi.hoisted(() => ({
  canUpload: vi.fn(),
  importBatch: vi.fn(),
  previewBatch: vi.fn(),
  push: vi.fn(),
  resetImport: vi.fn(),
  resetPreview: vi.fn(),
  sampleFile: vi.fn(),
  useDonorBatches: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push }),
}));

vi.mock("@/hooks/use-can", () => ({
  useCan: mocks.canUpload,
}));

vi.mock("@/hooks/use-donor-batches", () => ({
  getDonorBatchErrorMessage: (error: unknown, fallback: string) => {
    if (
      error &&
      typeof error === "object" &&
      "code" in error &&
      error.code === "PREVIEW_EXPIRED"
    ) {
      return "This upload preview has expired. Upload the file again to continue.";
    }
    return error instanceof Error ? error.message : fallback;
  },
  useDonorBatches: mocks.useDonorBatches,
  useImportDonorBatch: () => ({
    mutateAsync: mocks.importBatch,
    isPending: false,
    error: null,
    reset: mocks.resetImport,
  }),
  usePreviewDonorBatch: () => ({
    mutateAsync: mocks.previewBatch,
    isPending: false,
    error: null,
    reset: mocks.resetPreview,
  }),
  useSampleBatchFile: () => ({
    mutateAsync: mocks.sampleFile,
    isPending: false,
    error: null,
  }),
}));

function makePreview(overrides: Partial<BatchPreview> = {}): BatchPreview {
  return {
    preview_token: "preview-token",
    original_filename: "donors.csv",
    total_rows: 2,
    valid_rows: 1,
    invalid_rows: 1,
    segment_breakdown: [{ segment: "regular", count: 1 }],
    language_breakdown: [{ language: "en", count: 1 }],
    sample_valid_rows: [
      {
        row: 2,
        name: "Ayesha Khan",
        phone: "+923001234567",
        segment: "regular",
        language: "en",
        city: "Karachi",
        blood_group: "O+",
      },
    ],
    errors: [
      {
        row: 3,
        field: "phone",
        value: "0300-12",
        reason: "Invalid Pakistani mobile number",
      },
    ],
    warnings: [],
    ...overrides,
  };
}

const importedBatch: DonorBatch = {
  id: "batch-id",
  name: "October Recall",
  original_filename: "donors.csv",
  total_rows: 2,
  valid_rows: 1,
  invalid_rows: 1,
  uploaded_by: { id: "user-id", full_name: "Admin User" },
  created_at: "2026-10-04T10:00:00Z",
  campaign_count: 0,
};

describe("Donor batch pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.canUpload.mockReturnValue(true);
    mocks.previewBatch.mockResolvedValue(makePreview());
    mocks.importBatch.mockResolvedValue(importedBatch);
    mocks.useDonorBatches.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isPending: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  afterEach(cleanup);

  it("completes the upload, review, confirm, and success flow", async () => {
    const user = userEvent.setup();
    const { container } = render(<BatchUploadWizard />);

    await user.type(screen.getByLabelText("Batch name"), "October Recall");
    const input =
      container.querySelector<HTMLInputElement>('input[type="file"]');
    expect(input).not.toBeNull();
    await user.upload(
      input!,
      new File(["name,phone"], "donors.csv", { type: "text/csv" }),
    );
    await user.click(screen.getByRole("button", { name: "Review batch" }));

    expect(await screen.findByText("Ayesha Khan")).toBeVisible();
    expect(screen.getByText("O+")).toHaveAttribute("dir", "ltr");
    await user.click(
      screen.getByRole("button", { name: "Continue to confirm" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Import 1 valid donors" }),
    );
    const confirmButtons = screen.getAllByRole("button", {
      name: "Import 1 valid donors",
    });
    await user.click(confirmButtons.at(-1)!);

    expect(
      await screen.findByRole("heading", { name: "Batch imported" }),
    ).toBeVisible();
    expect(mocks.importBatch).toHaveBeenCalledWith({
      name: "October Recall",
      previewToken: "preview-token",
    });
  }, 15_000);

  it("disables import when a preview has no valid rows", () => {
    render(
      <ConfirmStep
        preview={makePreview({
          valid_rows: 0,
          invalid_rows: 2,
          sample_valid_rows: [],
        })}
        batchName="Bad donors"
        error={null}
        pending={false}
        onBack={vi.fn()}
        onConfirm={vi.fn()}
        onUploadAgain={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Import 0 valid donors" }),
    ).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("no valid donor rows");
  });

  it("offers upload-again recovery when the preview expired", () => {
    render(
      <ConfirmStep
        preview={makePreview()}
        batchName="October Recall"
        error={new ApiError(410, "PREVIEW_EXPIRED", "Preview expired")}
        pending={false}
        onBack={vi.fn()}
        onConfirm={vi.fn()}
        onUploadAgain={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "This upload preview has expired",
    );
    expect(screen.getByRole("button", { name: "Upload again" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Import 1 valid donors" }),
    ).toBeDisabled();
  });

  it("renders masked existing-phone warnings separately from errors", () => {
    render(
      <ReviewStep
        preview={makePreview({
          warnings: [
            {
              row: 2,
              phone: "+92300*****67",
              existing_batch_name: "January Recall",
            },
          ],
        })}
        onBack={vi.fn()}
        onContinue={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Existing donors found" }),
    ).toBeVisible();
    expect(screen.getByText("+92300*****67")).toBeVisible();
    expect(screen.getByText("January Recall")).toBeVisible();
    expect(screen.getByText(/valid and will be imported/i)).toBeVisible();
  });

  it("hides the upload action from coordinators", () => {
    mocks.canUpload.mockReturnValue(false);
    render(<BatchListScreen />);

    expect(
      screen.queryByRole("link", { name: /upload batch/i }),
    ).not.toBeInTheDocument();
  });
});
