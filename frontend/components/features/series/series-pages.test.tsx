import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useForm } from "react-hook-form";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ActivationProblems } from "@/components/features/series/activation-problems";
import { SeriesEditorScreen } from "@/components/features/series/series-editor-screen";
import { SeriesSettingsForm } from "@/components/features/series/series-settings-form";
import { SeriesStepButtonsFields } from "@/components/features/series/series-step-buttons-fields";
import { SeriesStepContentFields } from "@/components/features/series/series-step-content-fields";
import type { SeriesStepFormValues } from "@/components/features/series/series-step-form";
import type { ContentSeriesDetail } from "@/hooks/use-content-series";

const mocks = vi.hoisted(() => ({ canManage: vi.fn() }));
const idleMutation = {
  mutate: vi.fn(),
  mutateAsync: vi.fn(),
  isPending: false,
  error: null,
};

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/hooks/use-can", () => ({ useCan: mocks.canManage }));
vi.mock("@/hooks/use-content-series", () => ({
  getContentSeriesErrorMessage: (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback,
  getActivationProblems: () => [],
  useContentSeriesDetail: () => ({
    data: activeSeries,
    isPending: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateContentSeries: () => idleMutation,
  useReorderSeriesSteps: () => idleMutation,
  useSeriesPreview: () => ({
    data: previewMessage,
    isPending: false,
    error: null,
  }),
  useCreateSeriesStep: () => idleMutation,
  useUpdateSeriesStep: () => idleMutation,
  useDeleteSeriesStep: () => idleMutation,
  useUploadSeriesMedia: () => idleMutation,
  useActivateContentSeries: () => idleMutation,
  useArchiveContentSeries: () => idleMutation,
  useDuplicateContentSeries: () => idleMutation,
}));

const activeSeries: ContentSeriesDetail = {
  id: "series-id",
  name: "Regular Donor Recall",
  description: "Recall regular donors",
  kind: "primary",
  status: "active",
  languages: ["en", "ur"],
  response_window_hours: 48,
  tags: ["regular", "recall"],
  step_count: 1,
  created_by: { id: "user-id", full_name: "Admin User" },
  created_at: "2026-10-04T10:00:00Z",
  updated_at: "2026-10-04T10:00:00Z",
  steps: [
    {
      id: "step-id",
      step_order: 1,
      delay_days: 0,
      category: "utility",
      media_type: "none",
      media_url: null,
      contents: [
        { id: "content-en", language: "en", body: "Hello {{donor_name}}" },
        {
          id: "content-ur",
          language: "ur",
          body: "السلام علیکم {{donor_name}}",
        },
      ],
      buttons: [],
    },
  ],
};

const previewMessage = {
  id: "preview-id",
  donor_id: null,
  direction: "outbound" as const,
  kind: "template" as const,
  body: "Hello Ahmed Raza",
  media_type: "none" as const,
  media_url: null,
  buttons: [],
  status: "queued" as const,
  created_at: "2026-10-04T10:00:00Z",
};

function StepFieldsHarness({
  mode,
}: {
  mode: "content" | "buttons";
}): React.JSX.Element {
  const form = useForm<SeriesStepFormValues>({
    defaultValues: {
      delay_days: 0,
      category: "utility",
      media_type: "none",
      media_url: null,
      contents: { en: "Hello ", ur: "" },
      buttons: Array.from({ length: 3 }, () => ({
        intent: "confirm" as const,
        labels: { en: "Confirm", ur: "تصدیق" },
      })),
    },
  });
  return mode === "content" ? (
    <SeriesStepContentFields
      form={form}
      languages={["en", "ur"]}
      language="en"
      onLanguageChange={vi.fn()}
      readOnly={false}
    />
  ) : (
    <SeriesStepButtonsFields
      form={form}
      languages={["en", "ur"]}
      readOnly={false}
    />
  );
}

describe("Content series pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.canManage.mockReturnValue(true);
  });
  afterEach(cleanup);

  it("renders activation problems grouped by step and language", () => {
    render(
      <ActivationProblems
        problems={[
          {
            step: 1,
            language: "en",
            field: "body",
            reason: "Content is required",
          },
          {
            step: 1,
            language: "ur",
            field: "body",
            reason: "Content is required",
          },
          {
            step: 2,
            language: null,
            field: "media_url",
            reason: "Media URL is required",
          },
        ]}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Series needs attention" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Step 1 · English" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Step 1 · Urdu" }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { name: "Step 2" })).toBeVisible();
  });

  it("inserts an approved variable at the message caret", async () => {
    const user = userEvent.setup();
    render(<StepFieldsHarness mode="content" />);
    const body = screen.getByRole("textbox", {
      name: "English message body",
    }) as HTMLTextAreaElement;
    await user.click(body);
    body.setSelectionRange(body.value.length, body.value.length);
    await user.click(screen.getByRole("button", { name: "Insert Donor name" }));
    expect(body).toHaveValue("Hello {{donor_name}}");
  });

  it("enforces the three-button limit", () => {
    render(<StepFieldsHarness mode="buttons" />);
    expect(screen.getByRole("button", { name: "Add button" })).toBeDisabled();
    expect(
      screen.getByText("Maximum of 3 quick-reply buttons reached."),
    ).toBeVisible();
    expect(screen.getAllByLabelText(/Button \d English label/)).toHaveLength(3);
  });

  it("disables settings and mutation controls in read-only mode", () => {
    render(
      <SeriesSettingsForm
        series={{ ...activeSeries, status: "archived" }}
        readOnly
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Name")).toBeDisabled();
    expect(screen.getByLabelText("English")).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Save settings" }),
    ).not.toBeInTheDocument();
  });

  it("shows coordinators the complete editor as read-only", () => {
    mocks.canManage.mockReturnValue(false);
    render(<SeriesEditorScreen seriesId="series-id" />);
    expect(
      screen.getByText("Coordinator view: this content series is read-only."),
    ).toBeVisible();
    expect(screen.getByLabelText("Name")).toBeDisabled();
    expect(screen.getByRole("button", { name: /Step 1/ })).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Add step" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Activate series" }),
    ).not.toBeInTheDocument();
  });
});
